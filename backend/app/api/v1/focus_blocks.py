from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.database import supabase_client
from app.api.dependencies import get_current_user
from app.services.risk_service import recalculate_commitment_risk
from app.services.time_spine_service import advance_time_spine_stage, get_time_spine_view
from app.services.trace_service import AgentTraceLogger, create_agent_run, update_agent_run

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateFocusBlockRequest(BaseModel):
    commitment_id: str
    title: str
    start_at: datetime
    end_at: datetime
    block_type: str = "deep_work"


class UpdateFocusBlockRequest(BaseModel):
    title: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    block_type: Optional[str] = None
    status: Optional[str] = None


class CompleteFocusBlockRequest(BaseModel):
    actual_minutes: int = Field(..., ge=0)
    completion_status: str
    energy_level: int = Field(..., ge=1, le=5)
    quality_confidence: Optional[str] = None
    blocker_reason: Optional[str] = None
    notes: Optional[str] = None
    progress_percent_update: Optional[float] = Field(default=None, ge=0, le=100)


class SkipFocusBlockRequest(BaseModel):
    reason: str
    blocker_reason: Optional[str] = None
    notes: Optional[str] = None


def _require_db():
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized")


def _create_activity_trace(user_id: str, step_name: str, explanation: str, payload: Optional[dict] = None) -> None:
    """Persist a user-activity trace without tying focus lifecycle actions to a real AI run."""
    if not supabase_client:
        return
    try:
        run_id = create_agent_run(user_id, "user_activity", payload or {"step_name": step_name})
        if not run_id:
            return
        AgentTraceLogger(user_id, run_id).log(
            step_name,
            payload or {},
            status="succeeded",
            explanation=explanation,
        )
        update_agent_run(run_id, "completed", output_data={"step_name": step_name})
    except Exception as exc:  # Activity logs should not break user actions.
        logger.warning("Failed to write activity trace %s: %s", step_name, exc)


def _planned_minutes(block: dict) -> int:
    start_at = datetime.fromisoformat(str(block["start_at"]).replace("Z", "+00:00"))
    end_at = datetime.fromisoformat(str(block["end_at"]).replace("Z", "+00:00"))
    return max(0, int((end_at - start_at).total_seconds() // 60))


@router.get("", response_model=list[dict])
async def get_focus_blocks(user_id: str = Depends(get_current_user)):
    _require_db()
    res = (
        supabase_client.table("focus_blocks")
        .select("*")
        .eq("user_id", user_id)
        .order("start_at", desc=True)
        .execute()
    )
    return res.data or []


@router.post("")
async def create_focus_block(request: CreateFocusBlockRequest, user_id: str = Depends(get_current_user)):
    _require_db()

    comm_res = (
        supabase_client.table("commitments")
        .select("id,title")
        .eq("id", request.commitment_id)
        .eq("user_id", user_id)
        .execute()
    )
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
        "status": "scheduled",
    }

    res = supabase_client.table("focus_blocks").insert(block_data).execute()
    _create_activity_trace(
        user_id,
        "focus_block_created",
        f"Created focus block '{request.title}'.",
        {"commitment_id": request.commitment_id, "focus_block_id": block_data["id"]},
    )
    return res.data[0]


@router.patch("/{block_id}")
async def update_focus_block(block_id: str, request: UpdateFocusBlockRequest, user_id: str = Depends(get_current_user)):
    _require_db()
    update_data = request.model_dump(exclude_none=True)
    if "start_at" in update_data and update_data["start_at"] is not None:
        update_data["start_at"] = update_data["start_at"].isoformat()
    if "end_at" in update_data and update_data["end_at"] is not None:
        update_data["end_at"] = update_data["end_at"].isoformat()

    if not update_data:
        raise HTTPException(status_code=400, detail="No update fields provided")

    res = (
        supabase_client.table("focus_blocks")
        .update(update_data)
        .eq("id", block_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Focus block not found")
    return res.data[0]


@router.post("/{block_id}/start")
async def start_focus_block(block_id: str, user_id: str = Depends(get_current_user)):
    _require_db()

    res = (
        supabase_client.table("focus_blocks")
        .update({"status": "active"})
        .eq("id", block_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Focus block not found")

    _create_activity_trace(
        user_id,
        "focus_block_started",
        f"Started focus block '{res.data[0].get('title')}'.",
        {"focus_block_id": block_id, "commitment_id": res.data[0].get("commitment_id")},
    )
    return res.data[0]


@router.post("/{block_id}/complete")
async def complete_focus_block(block_id: str, request: CompleteFocusBlockRequest, user_id: str = Depends(get_current_user)):
    _require_db()

    block_res = (
        supabase_client.table("focus_blocks")
        .select("*")
        .eq("id", block_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not block_res.data:
        raise HTTPException(status_code=404, detail="Focus block not found")

    block = block_res.data
    commitment_id = block.get("commitment_id")
    if not commitment_id:
        raise HTTPException(status_code=400, detail="Focus block is not linked to a commitment")

    comm_res = (
        supabase_client.table("commitments")
        .select("*")
        .eq("id", commitment_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not comm_res.data:
        raise HTTPException(status_code=404, detail="Commitment not found")
    commitment = comm_res.data

    updated_block_res = (
        supabase_client.table("focus_blocks")
        .update({"status": "completed"})
        .eq("id", block_id)
        .eq("user_id", user_id)
        .execute()
    )

    planned_minutes = _planned_minutes(block)
    reflection_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "commitment_id": commitment_id,
        "focus_block_id": block_id,
        "planned_minutes": planned_minutes,
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
        .eq("id", commitment_id)
        .eq("user_id", user_id)
        .execute()
    )

    advance_time_spine_stage(commitment_id, user_id, event_type="focus_completed")
    time_spine = get_time_spine_view(commitment_id, user_id)

    _create_activity_trace(
        user_id,
        "focus_block_completed",
        f"Completed focus block for {request.actual_minutes}m. Progress {new_progress}%. Risk: {new_level}.",
        {"focus_block_id": block_id, "commitment_id": commitment_id, "reflection_id": reflection_data["id"]},
    )

    return {
        "focus_block": updated_block_res.data[0] if updated_block_res.data else {**block, "status": "completed"},
        "reflection": refl_res.data[0],
        "commitment": updated_comm.data[0],
        "risk": {"risk_score": new_score, "risk_level": new_level},
        "time_spine": time_spine,
    }


@router.post("/{block_id}/skip")
async def skip_focus_block(block_id: str, request: SkipFocusBlockRequest, user_id: str = Depends(get_current_user)):
    _require_db()

    block_res = (
        supabase_client.table("focus_blocks")
        .select("*")
        .eq("id", block_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not block_res.data:
        raise HTTPException(status_code=404, detail="Focus block not found")

    block = block_res.data
    commitment_id = block.get("commitment_id")
    if not commitment_id:
        raise HTTPException(status_code=400, detail="Focus block is not linked to a commitment")

    comm_res = (
        supabase_client.table("commitments")
        .select("*")
        .eq("id", commitment_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not comm_res.data:
        raise HTTPException(status_code=404, detail="Commitment not found")
    commitment = comm_res.data

    updated_block_res = (
        supabase_client.table("focus_blocks")
        .update({"status": "skipped"})
        .eq("id", block_id)
        .eq("user_id", user_id)
        .execute()
    )

    new_score, new_level = recalculate_commitment_risk(
        commitment,
        current_time=datetime.now(timezone.utc),
        skip_penalty=True,
    )

    updated_comm = (
        supabase_client.table("commitments")
        .update({"risk_score": new_score, "risk_level": new_level})
        .eq("id", commitment_id)
        .eq("user_id", user_id)
        .execute()
    )

    _create_activity_trace(
        user_id,
        "focus_block_skipped",
        f"Skipped focus block. Penalty applied. New risk: {new_level}.",
        {"focus_block_id": block_id, "commitment_id": commitment_id, **request.model_dump()},
    )

    return {
        "focus_block": updated_block_res.data[0] if updated_block_res.data else {**block, "status": "skipped"},
        "commitment": updated_comm.data[0],
        "risk": {"risk_score": new_score, "risk_level": new_level},
        "time_spine": get_time_spine_view(commitment_id, user_id),
    }
