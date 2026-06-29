from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.core.database import supabase_client
from app.services.capacity_service import get_layered_capacity
from app.services.rescue_service import find_rescue_candidates
from app.services.scheduling_graph import run_scheduling_graph
from app.services.scheduling_service import parse_iso

router = APIRouter()

_TERMINAL_COMMITMENT_STATUSES = {"completed", "archived"}
_DUE_SOON_WINDOW_HOURS = 24


def _end_of_today_utc(now: datetime) -> datetime:
    return now.replace(hour=23, minute=59, second=59, microsecond=0)


def _safe_parse_deadline(deadline_str: Optional[str]) -> Optional[datetime]:
    if not deadline_str:
        return None
    try:
        return parse_iso(deadline_str)
    except Exception:
        return None


def _remaining_minutes(commitment: Dict[str, Any]) -> int:
    estimated = int(commitment.get("estimated_minutes") or 0)
    actual = int(commitment.get("actual_minutes") or 0)
    return max(0, estimated - actual)


def _is_incomplete(commitment: Dict[str, Any]) -> bool:
    return commitment.get("status") not in _TERMINAL_COMMITMENT_STATUSES


def _calculate_time_health(
    commitments: List[Dict[str, Any]],
    available_minutes_today: int,
    now: datetime,
) -> Dict[str, Any]:
    """Deterministic, auditable Time Health calculation for the Command Brief."""
    next_24h = now + timedelta(hours=_DUE_SOON_WINDOW_HOURS)

    has_overdue_incomplete = False
    has_compromised_risk = False
    has_watch = False
    estimated_due_soon = 0
    top_risk_title = None

    for commitment in commitments:
        if not _is_incomplete(commitment):
            continue

        risk_level = commitment.get("risk_level") or "stable"
        deadline = _safe_parse_deadline(commitment.get("deadline_at"))

        if risk_level in {"rescue_required", "critical"}:
            has_compromised_risk = True
            top_risk_title = top_risk_title or commitment.get("title")
        elif risk_level == "watch":
            has_watch = True
            top_risk_title = top_risk_title or commitment.get("title")

        if deadline:
            if deadline < now:
                has_overdue_incomplete = True
                top_risk_title = top_risk_title or commitment.get("title")
            if deadline <= next_24h:
                has_watch = True
                estimated_due_soon += _remaining_minutes(commitment)
                top_risk_title = top_risk_title or commitment.get("title")

    if has_overdue_incomplete:
        return {
            "time_health": "Rescue Required",
            "time_health_explanation": "At least one deadline is slipping and needs intervention.",
            "estimated_minutes_due_soon": estimated_due_soon,
            "top_risk_title": top_risk_title,
        }

    if has_compromised_risk:
        return {
            "time_health": "Compromised",
            "time_health_explanation": "Your current workload exceeds available focus capacity.",
            "estimated_minutes_due_soon": estimated_due_soon,
            "top_risk_title": top_risk_title,
        }

    if estimated_due_soon > 0 and available_minutes_today < estimated_due_soon:
        return {
            "time_health": "Compromised",
            "time_health_explanation": "Your current workload exceeds available focus capacity.",
            "estimated_minutes_due_soon": estimated_due_soon,
            "top_risk_title": top_risk_title,
        }

    if has_watch:
        return {
            "time_health": "Watch",
            "time_health_explanation": "One or more commitments need attention soon.",
            "estimated_minutes_due_soon": estimated_due_soon,
            "top_risk_title": top_risk_title,
        }

    return {
        "time_health": "Stable",
        "time_health_explanation": "Your plan is currently executable.",
        "estimated_minutes_due_soon": estimated_due_soon,
        "top_risk_title": top_risk_title,
    }


def _count_pending_proposals(user_id: str) -> Dict[str, int]:
    res = (
        supabase_client.table("agent_proposed_actions")
        .select("id, action_type")
        .eq("user_id", user_id)
        .eq("status", "pending")
        .execute()
    )
    rows = res.data or []
    schedule_count = sum(1 for row in rows if row.get("action_type") == "create_focus_block")
    rescue_count = sum(1 for row in rows if row.get("action_type") == "commitment_rescue")
    return {
        "schedule_proposal_count": schedule_count,
        "rescue_proposal_count": rescue_count,
        "pending_approval_count": schedule_count + rescue_count,
    }


def _next_best_action(
    time_health: str,
    rescue_candidate_count: int,
    pending_approval_count: int,
    commitments_count: int,
) -> str:
    if pending_approval_count > 0:
        return f"ChronOS found {pending_approval_count} actions that need your approval."
    if time_health == "Rescue Required":
        return "Timeline compromised — run rescue plan."
    if rescue_candidate_count > 0:
        return f"ChronOS found {rescue_candidate_count} rescue candidates. Generate a rescue plan next."
    if commitments_count > 0:
        return "Start with the next safest block."
    return "No commitments yet. Add a brain dump or load the judge demo."


@router.post("/analyze")
def run_command_analysis(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")

    now = datetime.now(timezone.utc)
    today_end = _end_of_today_utc(now)

    commitments_res = supabase_client.table("commitments").select("*").eq("user_id", user_id).execute()
    commitments = commitments_res.data or []

    capacity_data = get_layered_capacity(user_id, today_end, now)
    available_minutes = int(capacity_data.get("available_minutes") or 0)
    capacity_source = capacity_data.get("capacity_source") or "mock"

    rescue_candidates = find_rescue_candidates(commitments, user_id)

    scheduling_result: Dict[str, Any] = {"success": False, "proposals_generated": 0}
    scheduling_warning = None
    if commitments:
        try:
            scheduling_state = run_scheduling_graph(user_id)
            if scheduling_state.get("error"):
                scheduling_warning = "Scheduling analysis could not complete. Existing data was still analyzed."
            else:
                scheduling_result = {
                    "success": True,
                    "agent_run_id": scheduling_state.get("agent_run_id"),
                    "proposals_generated": len(scheduling_state.get("proposals", [])),
                }
        except Exception:
            scheduling_warning = "Scheduling analysis could not complete. Existing data was still analyzed."

    health = _calculate_time_health(commitments, available_minutes, now)
    proposal_counts = _count_pending_proposals(user_id)
    warnings = [scheduling_warning] if scheduling_warning else []

    return {
        **health,
        "capacity_source": capacity_source,
        "available_minutes_today": available_minutes,
        "rescue_candidate_count": len(rescue_candidates),
        **proposal_counts,
        "next_best_action": _next_best_action(
            health["time_health"],
            len(rescue_candidates),
            proposal_counts["pending_approval_count"],
            len(commitments),
        ),
        "scheduling_result": scheduling_result,
        "warnings": warnings,
    }


@router.post("/demo/load")
def load_judge_demo(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Keep the operation idempotent for demo use. Clear only visible demo records;
    # never wipe the user's real commitments or pending non-demo approvals.
    supabase_client.table("focus_blocks").delete().eq("user_id", user_id).like("title", "%[DEMO]%").execute()
    supabase_client.table("agent_proposed_actions").delete().eq("user_id", user_id).filter("payload_json->>title", "ilike", "%[DEMO]%").execute()
    supabase_client.table("commitments").delete().eq("user_id", user_id).like("title", "[DEMO]%").execute()

    now = datetime.now(timezone.utc)
    demo_commitments = [
        {
            "user_id": user_id,
            "title": "[DEMO] Final Submission Build",
            "description": "The hackathon submission is due very soon. This creates an intentionally compromised timeline for the judge demo.",
            "type": "hard_deadline",
            "status": "active",
            "deadline_at": (now - timedelta(hours=2)).isoformat(),
            "estimated_minutes": 180,
            "actual_minutes": 0,
            "importance": 5,
            "flexibility": 1,
            "risk_level": "rescue_required",
            "risk_score": 95.0,
        },
        {
            "user_id": user_id,
            "title": "[DEMO] Record Demo Video",
            "description": "Record the 3-minute product walkthrough and upload it before submission.",
            "type": "hard_deadline",
            "status": "active",
            "deadline_at": (now + timedelta(hours=4)).isoformat(),
            "estimated_minutes": 60,
            "actual_minutes": 0,
            "importance": 5,
            "flexibility": 2,
            "risk_level": "watch",
            "risk_score": 60.0,
        },
        {
            "user_id": user_id,
            "title": "[DEMO] Polish Submission Writeup",
            "description": "Finalize the project description and architecture explanation.",
            "type": "soft_deadline",
            "status": "active",
            "deadline_at": (now + timedelta(days=1)).isoformat(),
            "estimated_minutes": 90,
            "actual_minutes": 10,
            "importance": 4,
            "flexibility": 3,
            "risk_level": "stable",
            "risk_score": 25.0,
        },
    ]

    insert_res = supabase_client.table("commitments").insert(demo_commitments).execute()
    inserted = insert_res.data or []

    return {
        "status": "Demo scenario loaded successfully.",
        "commitments_loaded": len(inserted) or len(demo_commitments),
    }
