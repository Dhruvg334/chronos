from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.core.database import supabase_client
from app.services.google_calendar_service import get_free_busy
from app.services.google_oauth_service import get_connection_status
from app.services.rescue_graph import run_rescue_graph
from app.services.rescue_service import find_rescue_candidates
from app.services.scheduling_service import detect_overlaps, parse_iso

router = APIRouter()

_ALLOWED_RESCUE_TYPES = {
    "create_rescue_focus_block",
    "defer_task",
    "compress_scope",
    "save_renegotiation_draft",
    "increase_focus_intensity",
    "renegotiate_deadline",
}


@router.get("/candidates")
def get_rescue_candidates(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    res = (
        supabase_client.table("commitments")
        .select("*, focus_blocks(*), tasks(*)")
        .eq("user_id", user_id)
        .execute()
    )
    commitments = res.data or []
    candidates = find_rescue_candidates(commitments, user_id)
    return {"candidates": candidates}


@router.post("/{commitment_id}/plan")
def generate_rescue_plan(commitment_id: str, user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    try:
        proposals = run_rescue_graph(user_id, commitment_id)
        return {"status": "plan_generated", "proposals": proposals}
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/plans")
def get_rescue_plans(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    res = (
        supabase_client.table("agent_proposed_actions")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "pending")
        .eq("action_type", "commitment_rescue")
        .execute()
    )
    return {"proposals": res.data or []}


def _get_pending_rescue_proposal(proposal_id: str, user_id: str) -> dict:
    res = (
        supabase_client.table("agent_proposed_actions")
        .select("*")
        .eq("id", proposal_id)
        .eq("user_id", user_id)
        .eq("action_type", "commitment_rescue")
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal = res.data[0]
    if proposal["status"] != "pending":
        raise HTTPException(status_code=400, detail="Proposal is no longer pending")
    payload = proposal.get("payload_json") or {}
    rescue_action_type = payload.get("rescue_action_type")
    if rescue_action_type not in _ALLOWED_RESCUE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid rescue action type")
    return proposal


@router.post("/proposals/{id}/approve")
def approve_rescue_proposal(id: str, user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    proposal = _get_pending_rescue_proposal(id, user_id)
    payload = proposal["payload_json"]
    rescue_action_type = payload["rescue_action_type"]

    created_focus_block = None
    if rescue_action_type == "create_rescue_focus_block":
        start_at = parse_iso(payload["start_at"])
        end_at = parse_iso(payload["end_at"])

        fb_res = (
            supabase_client.table("focus_blocks")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", ["scheduled", "active"])
            .execute()
        )
        existing_blocks = fb_res.data or []

        busy_windows = []
        status = get_connection_status(user_id)
        if status.get("connected"):
            busy_windows = get_free_busy(user_id, start_at, end_at) or []

        if detect_overlaps(start_at, end_at, existing_blocks, busy_windows):
            raise HTTPException(status_code=409, detail="Proposed rescue time overlaps with existing blocks or calendar events")

        insert_res = supabase_client.table("focus_blocks").insert({
            "commitment_id": payload["commitment_id"],
            "user_id": user_id,
            "title": payload["title"],
            "start_at": payload["start_at"],
            "end_at": payload["end_at"],
            "status": "scheduled",
            "block_type": "deep_work",
        }).execute()
        created_focus_block = insert_res.data[0] if insert_res.data else None

    # For defer/compress/draft actions, approval records the decision only. No destructive task mutation yet.
    supabase_client.table("agent_proposed_actions").update({"status": "approved"}).eq("id", id).eq("user_id", user_id).eq("action_type", "commitment_rescue").execute()
    return {"status": "approved", "action": rescue_action_type, "focus_block": created_focus_block}


@router.post("/proposals/{id}/reject")
def reject_rescue_proposal(id: str, user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    _get_pending_rescue_proposal(id, user_id)
    supabase_client.table("agent_proposed_actions").update({"status": "rejected"}).eq("id", id).eq("user_id", user_id).eq("action_type", "commitment_rescue").execute()
    return {"status": "rejected"}
