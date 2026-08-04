from fastapi import APIRouter, Depends, Header, HTTPException
from datetime import datetime, timezone
from typing import Optional
import uuid

from app.schemas.intake import (
    BrainDumpRequest,
    IntakeResponse,
    ApproveCommitmentsRequest,
    ApproveCommitmentsResponse,
)
from app.api.dependencies import get_current_user, get_model_gateway, get_repositories
from app.models.gateway import ModelGateway
from app.repositories.protocols import RepositorySet
from app.services.core_journey import calculate_core_risk
from app.core.config import settings
from app.core.observability import request_id_context
from app.workflows.intake import IntakeWorkflow
from app.workflows.runtime import WorkflowRunner
from app.services.usage_limits import UsageCategory, enforce_if_available

router = APIRouter(prefix="/api/v1/ai/intake", tags=["ai", "intake"])

VALID_COMMITMENT_TYPES = {
    "hard_deadline",
    "soft_deadline",
    "event",
    "habit",
    "waiting_on",
    "recurring_obligation",
    "reference",
    "someday",
}

PROJECT_LIKE_TYPES = {"project", "milestone", "assignment", "deliverable", "interview"}


def _normalize_commitment_type(raw_type: Optional[str]) -> str:
    value = (raw_type or "hard_deadline").strip().lower().replace(" ", "_").replace("-", "_")
    if value in VALID_COMMITMENT_TYPES:
        return value
    if value in PROJECT_LIKE_TYPES:
        return "hard_deadline"
    if value in {"task", "todo", "deliverable"}:
        return "hard_deadline"
    return "hard_deadline"


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _json_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


@router.post("", response_model=IntakeResponse)
async def process_intake(
    request: BrainDumpRequest,
    user_id: str = Depends(get_current_user),
    gateway: ModelGateway = Depends(get_model_gateway),
    repositories: RepositorySet = Depends(get_repositories),
):
    enforce_if_available(repositories.operations, user_id, UsageCategory.MODEL)
    workflow = IntakeWorkflow(
        gateway,
        WorkflowRunner(
            max_steps=settings.WORKFLOW_MAX_STEPS,
            timeout_seconds=settings.WORKFLOW_TIMEOUT_SECONDS,
            request_budget=settings.WORKFLOW_REQUEST_BUDGET,
            trace_repository=repositories.traces,
        ),
    )
    profile = repositories.planning_profiles.get(user_id)
    result, context = await workflow.extract(
        user_id=user_id,
        text=request.text,
        timezone_name=str(profile.get("timezone") or "UTC"),
        request_id=request_id_context.get(),
    )
    result.agent_run_id = uuid.UUID(context.run_id or context.workflow_id)
    return result


@router.post("/approve", response_model=ApproveCommitmentsResponse)
async def approve_intake(
    request: ApproveCommitmentsRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user_id: str = Depends(get_current_user),
    repositories: RepositorySet = Depends(get_repositories),
):
    if not request.approved_drafts:
        raise HTTPException(status_code=400, detail="No approved drafts provided.")

    agent_run_id = str(request.agent_run_id)
    items = []
    for draft in request.approved_drafts:
        if draft.project_id and not repositories.projects.get_for_user(user_id, str(draft.project_id)):
            raise HTTPException(status_code=400, detail="Selected project not found.")
        if draft.outcome_id and not repositories.outcomes.get_for_user(user_id, str(draft.outcome_id)):
            raise HTTPException(status_code=400, detail="Selected outcome not found.")
        deadline_at = _parse_dt(draft.deadline_at)
        start_before_at = _parse_dt(draft.start_before_at)
        risk_score, risk_level, warnings = calculate_core_risk(
            current_time=datetime.now(timezone.utc), deadline_at=deadline_at,
            estimated_minutes=draft.estimated_minutes, progress_percent=0.0,
            importance=draft.importance, flexibility=draft.flexibility,
            confidence_score=draft.confidence_score,
        )
        commitment_id = str(uuid.uuid4())
        item = {
            "id": commitment_id, "title": draft.title, "description": draft.done_condition,
            "type": _normalize_commitment_type(draft.type), "status": "active",
            "deadline_at": _json_dt(deadline_at), "start_before_at": _json_dt(start_before_at),
            "estimated_minutes": draft.estimated_minutes or 0, "actual_minutes": 0,
            "importance": draft.importance, "flexibility": draft.flexibility,
            "progress_percent": 0, "risk_score": risk_score, "risk_level": risk_level,
            "confidence_score": draft.confidence_score,
            "kind": draft.kind,
            "project_id": str(draft.project_id) if draft.project_id else None,
            "outcome_id": str(draft.outcome_id) if draft.outcome_id else None,
            "completion_criteria": draft.done_condition or f"{draft.title} is complete.",
            "minimum_viable_version": draft.next_action or f"Do a five-minute version of {draft.title}.",
            "preferred_days": repositories.planning_profiles.get(user_id).get("available_weekdays", [0, 1, 2, 3, 4]),
            "tasks": [{
                "id": str(uuid.uuid4()), "title": task.title,
                "next_action": getattr(task, "next_action", None),
                "done_condition": getattr(task, "done_condition", None),
                "status": "pending", "estimated_minutes": task.estimated_minutes or 0,
                "sequence_order": index,
            } for index, task in enumerate(draft.tasks)],
            "warning_count": len(warnings),
        }
        checkpoints = [
            {"id": "capture", "status": "completed", "label": "Captured"},
            {"id": "clarify", "status": "completed", "label": "Clarified"},
            {"id": "next_action", "status": "pending", "label": "Next Action"},
        ]
        is_major = (draft.estimated_minutes or 0) >= 240 or _normalize_commitment_type(draft.type) in {"hard_deadline", "soft_deadline"}
        if is_major:
            checkpoints.extend([
                {"id": "milestone", "status": "pending", "label": "Milestone"},
                {"id": "feedback_gate", "status": "pending", "label": "Feedback Gate"},
            ])
        checkpoints.extend([
            {"id": "buffer", "status": "pending", "label": "Buffer Zone"},
            {"id": "final_deadline", "status": "pending", "label": "Final Deadline"},
            {"id": "reflection", "status": "pending", "label": "Reflection"},
        ])
        item["time_spine"] = {"id": str(uuid.uuid4()), "stages": checkpoints, "current_stage": "next_action"}
        items.append(item)

    key = idempotency_key or f"intake-{agent_run_id}"
    result = repositories.commitments.approve_intake(user_id, agent_run_id, key, items)
    count = int(result["count"])
    return ApproveCommitmentsResponse(status="success", count=count, message=f"Successfully approved {count} planning items.")
