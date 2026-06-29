from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List
from datetime import datetime, timezone

from app.api.dependencies import get_current_user
from app.core.database import supabase_client
from app.services.scheduling_graph import run_scheduling_graph
from app.services.scheduling_service import detect_overlaps, parse_iso
from app.services.google_calendar_service import get_free_busy
from app.services.google_oauth_service import get_connection_status

router = APIRouter()

@router.post("/plan")
def plan_schedule(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Run the planning graph and generate proposed actions."""
    final_state = run_scheduling_graph(user_id)
    if final_state.get("error"):
        raise HTTPException(status_code=500, detail=final_state["error"])
        
    return {
        "success": True,
        "agent_run_id": final_state.get("agent_run_id"),
        "proposals_generated": len(final_state.get("proposals", []))
    }

@router.get("/proposals")
def get_proposals(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Get all pending proposals for the user."""
    res = supabase_client.table("agent_proposed_actions")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("status", "pending")\
        .eq("action_type", "create_focus_block")\
        .order("created_at", desc=False)\
        .execute()
        
    return {"proposals": res.data or []}

def approve_single_proposal(user_id: str, proposal_id: str) -> Dict[str, Any]:
    """Internal function to approve a proposal. Returns the created focus block."""
    res = supabase_client.table("agent_proposed_actions").select("*").eq("id", proposal_id).eq("user_id", user_id).single().execute()
    if not res.data:
        raise ValueError("Proposal not found or unauthorized")
        
    proposal = res.data
    if proposal["status"] != "pending":
        raise ValueError(f"Proposal is already {proposal['status']}")
        
    payload = proposal["payload_json"]
    start_at = parse_iso(payload["start_at"])
    end_at = parse_iso(payload["end_at"])
    
    # Re-validate overlaps
    now = datetime.now(timezone.utc).isoformat()
    fb_res = supabase_client.table("focus_blocks").select("*").eq("user_id", user_id).in_("status", ["scheduled", "active"]).gte("end_at", now).execute()
    existing_blocks = fb_res.data or []
    
    # Fetch busy windows for this small range
    busy_windows = []
    status = get_connection_status(user_id)
    if status.get("connected"):
        busy = get_free_busy(user_id, start_at, end_at)
        busy_windows = busy or []
    
    if detect_overlaps(start_at, end_at, existing_blocks, busy_windows):
        # Overlaps detected! Reject automatically
        supabase_client.table("agent_proposed_actions").update({"status": "rejected", "explanation": "Validation failed: Overlaps detected at approval time"}).eq("id", proposal_id).execute()
        raise ValueError("Overlaps detected. Proposal is no longer valid.")
        
    # Create focus block
    fb_payload = {
        "user_id": user_id,
        "commitment_id": payload["commitment_id"],
        "title": payload["title"],
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "block_type": "deep_work", # default
        "status": "scheduled"
    }
    fb_insert = supabase_client.table("focus_blocks").insert(fb_payload).execute()
    new_block = fb_insert.data[0]
    
    # Mark approved
    supabase_client.table("agent_proposed_actions").update({"status": "approved"}).eq("id", proposal_id).execute()
    
    return new_block

@router.post("/proposals/{proposal_id}/approve")
def approve_proposal(proposal_id: str, user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    try:
        new_block = approve_single_proposal(user_id, proposal_id)
        return {"success": True, "focus_block": new_block}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/proposals/{proposal_id}/reject")
def reject_proposal(proposal_id: str, user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    res = supabase_client.table("agent_proposed_actions").select("status").eq("id", proposal_id).eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Proposal not found")
        
    supabase_client.table("agent_proposed_actions").update({"status": "rejected", "explanation": "Rejected by user"}).eq("id", proposal_id).execute()
    return {"success": True}

@router.post("/proposals/approve-all")
def approve_all_proposals(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    res = supabase_client.table("agent_proposed_actions").select("id").eq("user_id", user_id).eq("status", "pending").execute()
    proposals = res.data or []
    
    applied = []
    skipped = []
    
    for p in proposals:
        try:
            new_block = approve_single_proposal(user_id, p["id"])
            applied.append(new_block)
        except Exception as e:
            skipped.append({"id": p["id"], "reason": str(e)})
            
    return {
        "success": True,
        "applied": applied,
        "skipped": skipped
    }
