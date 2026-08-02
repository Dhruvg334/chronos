from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from app.api.dependencies import get_current_user, get_repositories
from app.core.errors import ChronosError, ErrorCode
from app.repositories.protocols import RepositorySet
from app.schemas.core import CompleteFocusRequest, FocusSessionResponse, StartFocusRequest, StopFocusRequest, StuckResponse
from app.services.core_journey import focus_view, observed_risk, parse_datetime

router = APIRouter()

STUCK_OPTIONS = (
    "Define a smaller next step",
    "Identify missing information",
    "Switch to a short setup action",
    "Request a recovery suggestion",
)


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


def _get_block(repositories: RepositorySet, user_id: str, block_id: str) -> dict:
    block = repositories.focus.get_for_user(user_id, block_id)
    if not block:
        raise ChronosError(ErrorCode.VALIDATION, "Focus session not found.")
    return block


def _advance_spine(repositories: RepositorySet, user_id: str, commitment_id: str) -> dict | None:
    spine = repositories.commitments.get_time_spine(user_id, commitment_id)
    if not spine:
        return None
    stages = list(spine.get("spine_json") or [])
    for stage in stages:
        if stage.get("id") == "next_action":
            stage["status"] = "completed"
    return repositories.commitments.update_time_spine(user_id, commitment_id, {"spine_json": stages, "current_stage": "reflection"})


@router.get("", response_model=list[dict])
async def get_focus_blocks(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return repositories.focus.list_for_user(user_id)


@router.post("/start", response_model=FocusSessionResponse)
async def start_contextual_focus(request: StartFocusRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    if repositories.focus.get_active(user_id):
        raise ChronosError(ErrorCode.CONFLICT, "Finish or stop the active focus session before starting another.")
    commitment = repositories.commitments.get_for_user(user_id, request.commitment_id)
    if not commitment:
        raise ChronosError(ErrorCode.VALIDATION, "Commitment not found.")
    now = datetime.now(timezone.utc)
    block = repositories.focus.create(user_id, {
        "id": str(uuid.uuid4()),
        "commitment_id": request.commitment_id,
        "title": request.title or str(commitment["title"]),
        "start_at": now.isoformat(),
        "end_at": (now + timedelta(minutes=request.duration_minutes)).isoformat(),
        "block_type": "deep_work",
        "status": "active",
        "started_at": now.isoformat(),
        "accumulated_pause_seconds": 0,
    })
    return FocusSessionResponse(session=focus_view(block, now=now))


@router.post("")
async def create_focus_block(request: CreateFocusBlockRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    if request.end_at <= request.start_at:
        raise ChronosError(ErrorCode.VALIDATION, "Focus block end time must be after its start time.")
    if not repositories.commitments.get_for_user(user_id, request.commitment_id):
        raise ChronosError(ErrorCode.VALIDATION, "Commitment not found.")
    return repositories.focus.create(user_id, {
        "id": str(uuid.uuid4()),
        "commitment_id": request.commitment_id,
        "title": request.title,
        "start_at": request.start_at.isoformat(),
        "end_at": request.end_at.isoformat(),
        "block_type": request.block_type,
        "status": "scheduled",
    })


@router.patch("/{block_id}")
async def update_focus_block(block_id: str, request: UpdateFocusBlockRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    update = request.model_dump(exclude_none=True)
    if not update:
        raise ChronosError(ErrorCode.VALIDATION, "No update fields were provided.")
    if isinstance(update.get("start_at"), datetime):
        update["start_at"] = update["start_at"].isoformat()
    if isinstance(update.get("end_at"), datetime):
        update["end_at"] = update["end_at"].isoformat()
    return repositories.focus.update(user_id, block_id, update)


@router.post("/{block_id}/start", response_model=FocusSessionResponse)
async def start_focus_block(block_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    existing = repositories.focus.get_active(user_id)
    if existing and str(existing["id"]) != block_id:
        raise ChronosError(ErrorCode.CONFLICT, "Finish or stop the active focus session before starting another.")
    block = _get_block(repositories, user_id, block_id)
    now = datetime.now(timezone.utc)
    updated = repositories.focus.update(user_id, block_id, {"status": "active", "started_at": block.get("started_at") or now.isoformat(), "paused_at": None})
    return FocusSessionResponse(session=focus_view(updated, now=now))


@router.post("/{block_id}/pause", response_model=FocusSessionResponse)
async def pause_focus_block(block_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    block = _get_block(repositories, user_id, block_id)
    if block.get("status") != "active":
        raise ChronosError(ErrorCode.CONFLICT, "Only an active focus session can be paused.")
    now = datetime.now(timezone.utc)
    updated = repositories.focus.update(user_id, block_id, {"status": "paused", "paused_at": now.isoformat()})
    return FocusSessionResponse(session=focus_view(updated, now=now))


@router.post("/{block_id}/resume", response_model=FocusSessionResponse)
async def resume_focus_block(block_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    block = _get_block(repositories, user_id, block_id)
    if block.get("status") != "paused" or not block.get("paused_at"):
        raise ChronosError(ErrorCode.CONFLICT, "Only a paused focus session can be resumed.")
    now = datetime.now(timezone.utc)
    paused_seconds = max(0, int((now - parse_datetime(block["paused_at"])).total_seconds()))
    updated = repositories.focus.update(user_id, block_id, {"status": "active", "paused_at": None, "accumulated_pause_seconds": int(block.get("accumulated_pause_seconds") or 0) + paused_seconds})
    return FocusSessionResponse(session=focus_view(updated, now=now))


@router.post("/{block_id}/stuck", response_model=StuckResponse)
async def focus_stuck(block_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    block = _get_block(repositories, user_id, block_id)
    if block.get("status") not in {"active", "paused"}:
        raise ChronosError(ErrorCode.CONFLICT, "Stuck guidance is available during an active focus session.")
    return StuckResponse(focus_block_id=block_id, options=STUCK_OPTIONS, recovery_available=True)


@router.post("/{block_id}/complete", response_model=FocusSessionResponse)
async def complete_focus_block(request: CompleteFocusRequest, block_id: str, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    block = _get_block(repositories, user_id, block_id)
    commitment_id = block.get("commitment_id")
    commitment = repositories.commitments.get_for_user(user_id, commitment_id) if commitment_id else None
    if not commitment:
        raise ChronosError(ErrorCode.VALIDATION, "The focus session is not linked to an available commitment.")
    risk_score, risk_level = observed_risk(commitment, progress_percent=request.progress_percent)
    result = repositories.focus.complete_transaction(user_id, {
        "p_focus_block_id": block_id,
        "p_reflection_id": str(uuid.uuid4()),
        "p_idempotency_key": idempotency_key or f"focus-{block_id}-{request.actual_minutes}-{request.progress_percent}",
        "p_actual_minutes": request.actual_minutes,
        "p_completion_status": request.completion_status,
        "p_energy_level": request.energy_level,
        "p_progress_percent": request.progress_percent,
        "p_risk_score": risk_score,
        "p_risk_level": risk_level,
        "p_blocker_reason": request.blocker_reason,
        "p_notes": request.notes,
    })
    return FocusSessionResponse(session=None, reflection=result.get("reflection"), reflection_requested=False)


@router.post("/{block_id}/skip", response_model=FocusSessionResponse)
async def skip_focus_block(request: StopFocusRequest, block_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    block = _get_block(repositories, user_id, block_id)
    commitment_id = block.get("commitment_id")
    commitment = repositories.commitments.get_for_user(user_id, commitment_id) if commitment_id else None
    repositories.focus.update(user_id, block_id, {"status": "skipped", "paused_at": None, "stopped_reason": request.reason})
    if commitment:
        risk_score, risk_level = observed_risk(commitment, progress_percent=int(commitment.get("progress_percent") or 0), skipped=True)
        repositories.commitments.update(user_id, commitment_id, {"risk_score": risk_score, "risk_level": risk_level})
    return FocusSessionResponse(session=None, reflection_requested=True)
