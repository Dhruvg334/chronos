from datetime import datetime, timezone
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.database import supabase_client
from app.api.dependencies import get_current_user
from app.services.risk_service import recalculate_commitment_risk
from app.services.time_spine_service import advance_time_spine_stage, get_time_spine_view
from app.services.trace_service import AgentTraceLogger, create_agent_run, update_agent_run

router = APIRouter()


class CreateReflectionRequest(BaseModel):
    commitment_id: str
    focus_block_id: Optional[str] = None
    planned_minutes: int = Field(..., ge=0)
    actual_minutes: int = Field(..., ge=0)
    completion_status: str
    energy_level: int = Field(..., ge=1, le=5)
    blocker_reason: Optional[str] = None
    quality_confidence: Optional[str] = None
    notes: Optional[str] = None
    progress_percent_update: Optional[float] = Field(default=None, ge=0, le=100)


def _require_db():
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized")


def _log_activity(user_id: str, step_name: str, explanation: str, payload: dict) -> None:
    if not supabase_client:
        return
    try:
        run_id = create_agent_run(user_id, "user_activity", payload)
        if not run_id:
            return
        AgentTraceLogger(user_id, run_id).log(step_name, payload, explanation=explanation)
        update_agent_run(run_id, "completed", output_data={"step_name": step_name})
    except Exception as exc:
        print(f"Failed to log activity {step_name}: {exc}")


@router.post("")
async def submit_reflection(request: CreateReflectionRequest, user_id: str = Depends(get_current_user)):
    _require_db()

    comm_res = (
        supabase_client.table("commitments")
        .select("*")
        .eq("id", request.commitment_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not comm_res.data:
        raise HTTPException(status_code=404, detail="Commitment not found")

    if request.focus_block_id:
        block_res = (
            supabase_client.table("focus_blocks")
            .select("id")
            .eq("id", request.focus_block_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not block_res.data:
            raise HTTPException(status_code=404, detail="Focus block not found")

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
        "notes": request.notes,
    }
    refl_res = supabase_client.table("reflections").insert(reflection_data).execute()

    new_actual = int(commitment.get("actual_minutes") or 0) + request.actual_minutes
    new_progress = (
        float(request.progress_percent_update)
        if request.progress_percent_update is not None
        else float(commitment.get("progress_percent") or 0.0)
    )

    commitment_for_risk = {**commitment, "actual_minutes": new_actual, "progress_percent": new_progress}
    new_score, new_level = recalculate_commitment_risk(commitment_for_risk, current_time=datetime.now(timezone.utc))

    updated_comm = (
        supabase_client.table("commitments")
        .update({
            "actual_minutes": new_actual,
            "progress_percent": new_progress,
            "risk_score": new_score,
            "risk_level": new_level,
        })
        .eq("id", request.commitment_id)
        .eq("user_id", user_id)
        .execute()
    )

    advance_time_spine_stage(request.commitment_id, user_id, event_type="reflection_submitted")
    time_spine = get_time_spine_view(request.commitment_id, user_id)

    _log_activity(
        user_id,
        "reflection_submitted",
        f"Reflection submitted. Progress {new_progress}%. Risk: {new_level}.",
        {"commitment_id": request.commitment_id, "reflection_id": reflection_data["id"]},
    )

    return {
        "reflection": refl_res.data[0],
        "commitment": updated_comm.data[0],
        "risk": {"risk_score": new_score, "risk_level": new_level},
        "time_spine": time_spine,
    }
