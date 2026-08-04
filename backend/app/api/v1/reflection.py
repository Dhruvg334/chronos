from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_repositories
from app.core.errors import ChronosError, ErrorCode
from app.repositories.protocols import RepositorySet
from app.schemas.core import ReflectionRequest
from app.services.core_journey import observed_risk
from app.services.context_service import MemoryService

router = APIRouter()


@router.post("")
async def submit_reflection(request: ReflectionRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    commitment = repositories.commitments.get_for_user(user_id, request.commitment_id)
    if not commitment:
        raise ChronosError(ErrorCode.VALIDATION, "Commitment not found.")
    if request.focus_block_id and not repositories.focus.get_for_user(user_id, request.focus_block_id):
        raise ChronosError(ErrorCode.VALIDATION, "Focus session not found.")
    reflection = repositories.reflections.create(user_id, {
        "id": str(uuid.uuid4()), "commitment_id": request.commitment_id, "focus_block_id": request.focus_block_id,
        "planned_minutes": request.planned_minutes, "actual_minutes": request.actual_minutes,
        "completion_status": request.completion_status, "energy_level": request.energy_level,
        "blocker_reason": request.blocker_reason, "notes": request.notes,
    })
    actual = int(commitment.get("actual_minutes") or 0) + request.actual_minutes
    progress = request.progress_percent if request.progress_percent is not None else int(commitment.get("progress_percent") or 0)
    risk_score, risk_level = observed_risk(commitment, progress_percent=progress, skipped=request.completion_status == "skipped")
    updated = repositories.commitments.update(user_id, request.commitment_id, {"actual_minutes": actual, "progress_percent": progress, "risk_score": risk_score, "risk_level": risk_level})
    spine = repositories.commitments.get_time_spine(user_id, request.commitment_id)
    if spine:
        stages = list(spine.get("spine_json") or [])
        for stage in stages:
            if stage.get("id") == "reflection":
                stage["status"] = "completed"
        spine = repositories.commitments.update_time_spine(user_id, request.commitment_id, {"spine_json": stages, "current_stage": "reflection"})
    try:
        memory_proposal = MemoryService(repositories).propose_from_reflection(user_id, reflection)
    except Exception:
        # Reflection persistence remains successful when optional context learning is unavailable.
        memory_proposal = None
    return {"reflection": reflection, "commitment": updated, "risk": {"risk_score": risk_score, "risk_level": risk_level}, "time_spine": spine, "memory_proposal": memory_proposal}
