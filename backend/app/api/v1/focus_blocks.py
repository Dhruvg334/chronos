from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid
import logging

from app.core.database import supabase_client
from app.api.dependencies import get_current_user
from app.services.risk_service import recalculate_commitment_risk
from app.services.time_spine_service import advance_time_spine_stage

router = APIRouter()
logger = logging.getLogger(__name__)

class CreateFocusBlockRequest(BaseModel):
    commitment_id: str
    title: str
    start_at: datetime
    end_at: datetime
    block_type: str = "deep_work"

class CompleteFocusBlockRequest(BaseModel):
    actual_minutes: int
    completion_status: str
    energy_level: int
    quality_confidence: Optional[str] = None
    blocker_reason: Optional[str] = None
    notes: Optional[str] = None
    progress_percent_update: Optional[float] = None

class SkipFocusBlockRequest(BaseModel):
    reason: str
    blocker_reason: Optional[str] = None
    notes: Optional[str] = None


@router.get("", response_model=list[dict])
async def get_focus_blocks(user_id: str = Depends(get_current_user)):
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized")
    res = supabase_client.table("focus_blocks").select("*").eq("user_id", user_id).order("start_at", desc=True).execute()
    return res.data


@router.post("")
async def create_focus_block(request: CreateFocusBlockRequest, user_id: str = Depends(get_current_user)):
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized")
        
    # Verify commitment ownership
    comm_res = supabase_client.table("commitments").select("id").eq("id", request.commitment_id).eq("user_id", user_id).execute()
    if not comm_res.data:
        raise HTTPException(status_code=404, detail="Commitment not found")

    block_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "commitment_id": request.commitment_id,
        "title": request.title,
        "start_at": request.start_at.isoformat(),
        "end_at": request.end_at.isoformat(),
        "block_type": request.block_type,
        "status": "scheduled"
    }
    
    res = supabase_client.table("focus_blocks").insert(block_data).execute()
    return res.data[0]


@router.patch("/{block_id}")
async def update_focus_block(block_id: str, request: dict, user_id: str = Depends(get_current_user)):
    # simple update for title, start, end
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized")
        
    res = supabase_client.table("focus_blocks").update(request).eq("id", block_id).eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Focus block not found")
    return res.data[0]


@router.post("/{block_id}/start")
async def start_focus_block(block_id: str, user_id: str = Depends(get_current_user)):
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized")
        
    res = supabase_client.table("focus_blocks").update({
        "status": "active",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", block_id).eq("user_id", user_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Focus block not found")
        
    return res.data[0]


@router.post("/{block_id}/complete")
async def complete_focus_block(block_id: str, request: CompleteFocusBlockRequest, user_id: str = Depends(get_current_user)):
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized")
        
    # 1. Validate focus block
    block_res = supabase_client.table("focus_blocks").select("*").eq("id", block_id).eq("user_id", user_id).single().execute()
    if not block_res.data:
        raise HTTPException(status_code=404, detail="Focus block not found")
    
    block = block_res.data
    commitment_id = block.get("commitment_id")
    
    # Fetch commitment
    comm_res = supabase_client.table("commitments").select("*").eq("id", commitment_id).single().execute()
    if not comm_res.data:
        raise HTTPException(status_code=404, detail="Commitment not found")
    commitment = comm_res.data

    # 2. Mark focus block completed
    supabase_client.table("focus_blocks").update({"status": "completed"}).eq("id", block_id).execute()
    
    # 3. Insert reflection row
    reflection_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "commitment_id": commitment_id,
        "focus_block_id": block_id,
        "planned_minutes": (datetime.fromisoformat(block["end_at"]) - datetime.fromisoformat(block["start_at"])).total_seconds() // 60,
        "actual_minutes": request.actual_minutes,
        "completion_status": request.completion_status,
        "energy_level": request.energy_level,
        "blocker_reason": request.blocker_reason,
        "quality_confidence": request.quality_confidence,
        "notes": request.notes
    }
    refl_res = supabase_client.table("reflections").insert(reflection_data).execute()

    # 4. Update commitment
    new_actual = int(commitment.get("actual_minutes", 0)) + request.actual_minutes
    new_progress = float(request.progress_percent_update) if request.progress_percent_update is not None else float(commitment.get("progress_percent", 0.0))
    
    commitment["actual_minutes"] = new_actual
    commitment["progress_percent"] = new_progress
    
    # 5. Recalculate deterministic risk
    new_score, new_level = recalculate_commitment_risk(commitment, current_time=datetime.now(timezone.utc))
    
    updated_comm = supabase_client.table("commitments").update({
        "actual_minutes": new_actual,
        "progress_percent": new_progress,
        "risk_score": new_score,
        "risk_level": new_level
    }).eq("id", commitment_id).execute()

    # 6. Update time spine stage (advance progress)
    advance_time_spine_stage(commitment_id, user_id)

    # 7. Persist trace/activity
    trace_data = {
        "user_id": user_id,
        "agent_run_id": None, # Null for manual activity? We might need an activity log or we can use trace table. Let's use trace with a special run_id or just insert.
        "step_name": "focus_block_completed",
        "status": "succeeded",
        "explanation": f"Completed block for {request.actual_minutes}m. Progress {new_progress}%. Risk: {new_level}.",
        "payload_json": request.model_dump()
    }
    # agent_run_id is required in the DB maybe?
    # No, agent_run_id is not strictly required if we mock one, or we create a dummy run. Let's create a dummy run for "activity".
    run_res = supabase_client.table("agent_runs").insert({
        "user_id": user_id,
        "run_type": "user_activity",
        "status": "completed"
    }).execute()
    trace_data["agent_run_id"] = run_res.data[0]["id"]
    supabase_client.table("agent_trace_events").insert(trace_data).execute()

    return {
        "focus_block": block,
        "reflection": refl_res.data[0],
        "commitment": updated_comm.data[0]
    }


@router.post("/{block_id}/skip")
async def skip_focus_block(block_id: str, request: SkipFocusBlockRequest, user_id: str = Depends(get_current_user)):
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized")
        
    block_res = supabase_client.table("focus_blocks").select("*").eq("id", block_id).eq("user_id", user_id).single().execute()
    if not block_res.data:
        raise HTTPException(status_code=404, detail="Focus block not found")
        
    block = block_res.data
    commitment_id = block.get("commitment_id")
    
    comm_res = supabase_client.table("commitments").select("*").eq("id", commitment_id).single().execute()
    commitment = comm_res.data
    
    # Mark skipped
    supabase_client.table("focus_blocks").update({"status": "skipped"}).eq("id", block_id).execute()
    
    # Recalculate risk with skip penalty
    new_score, new_level = recalculate_commitment_risk(commitment, current_time=datetime.now(timezone.utc), skip_penalty=True)
    
    updated_comm = supabase_client.table("commitments").update({
        "risk_score": new_score,
        "risk_level": new_level
    }).eq("id", commitment_id).execute()
    
    # Log trace
    run_res = supabase_client.table("agent_runs").insert({
        "user_id": user_id,
        "run_type": "user_activity",
        "status": "completed"
    }).execute()
    supabase_client.table("agent_trace_events").insert({
        "user_id": user_id,
        "agent_run_id": run_res.data[0]["id"],
        "step_name": "focus_block_skipped",
        "status": "succeeded",
        "explanation": f"Skipped block. Penalty applied. New risk: {new_level}.",
        "payload_json": request.model_dump()
    }).execute()

    return {
        "focus_block": block,
        "commitment": updated_comm.data[0]
    }
