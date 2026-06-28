from fastapi import APIRouter, Depends, HTTPException
from app.core.database import supabase_client
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/runs/{agent_run_id}/trace")
async def get_agent_traces(agent_run_id: str, user_id: str = Depends(get_current_user)):
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized")

    res = (
        supabase_client.table("agent_trace_events")
        .select("*")
        .eq("agent_run_id", agent_run_id)
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .execute()
    )
    return {"events": res.data or []}

@router.post("/proposed/{action_id}/approve")
async def approve_proposed_action(action_id: str, user_id: str = Depends(get_current_user)):
    return {"message": f"Mock approved action {action_id}", "user_id": user_id}

@router.post("/proposed/{action_id}/reject")
async def reject_proposed_action(action_id: str, user_id: str = Depends(get_current_user)):
    return {"message": f"Mock rejected action {action_id}", "user_id": user_id}
