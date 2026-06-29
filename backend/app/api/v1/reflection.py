from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from app.core.database import supabase_client
from app.api.dependencies import get_current_user
from app.services.risk_service import recalculate_commitment_risk
from app.services.time_spine_service import advance_time_spine_stage

router = APIRouter()

class CreateReflectionRequest(BaseModel):
    commitment_id: str
    focus_block_id: Optional[str] = None
    planned_minutes: int
    actual_minutes: int
    completion_status: str
    energy_level: int
    blocker_reason: Optional[str] = None
    quality_confidence: Optional[str] = None
    notes: Optional[str] = None
    progress_percent_update: Optional[float] = None

@router.post("")
async def submit_reflection(request: CreateReflectionRequest, user_id: str = Depends(get_current_user)):
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized")

    # Fetch commitment
    comm_res = supabase_client.table("commitments").select("*").eq("id", request.commitment_id).eq("user_id", user_id).single().execute()
    if not comm_res.data:
        raise HTTPException(status_code=404, detail="Commitment not found")
        
    commitment = comm_res.data
    
    reflection_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "commitment_id": request.commitment_id,
        "focus_block_id": request.focus_block_id,
        "planned_minutes": request.planned_minutes,
        "actual_minutes": request.actual_minutes,
        "completion_status": request.completion_status,
        "energy_level": request.energy_level,
        "blocker_reason": request.blocker_reason,
        "quality_confidence": request.quality_confidence,
        "notes": request.notes
    }
    refl_res = supabase_client.table("reflections").insert(reflection_data).execute()

    # Update commitment
    new_actual = int(commitment.get("actual_minutes", 0)) + request.actual_minutes
    new_progress = float(request.progress_percent_update) if request.progress_percent_update is not None else float(commitment.get("progress_percent", 0.0))
    
    commitment["actual_minutes"] = new_actual
    commitment["progress_percent"] = new_progress
    
    new_score, new_level = recalculate_commitment_risk(commitment, current_time=datetime.now(timezone.utc))
    
    updated_comm = supabase_client.table("commitments").update({
        "actual_minutes": new_actual,
        "progress_percent": new_progress,
        "risk_score": new_score,
        "risk_level": new_level
    }).eq("id", request.commitment_id).execute()

    advance_time_spine_stage(request.commitment_id, user_id)

    run_res = supabase_client.table("agent_runs").insert({
        "user_id": user_id,
        "run_type": "user_activity",
        "status": "completed"
    }).execute()
    
    supabase_client.table("agent_trace_events").insert({
        "user_id": user_id,
        "agent_run_id": run_res.data[0]["id"],
        "step_name": "reflection_submitted",
        "status": "succeeded",
        "explanation": f"Reflection submitted. Progress {new_progress}%. Risk: {new_level}.",
        "payload_json": request.model_dump()
    }).execute()

    return {
        "reflection": refl_res.data[0],
        "commitment": updated_comm.data[0]
    }
