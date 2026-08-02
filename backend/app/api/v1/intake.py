from fastapi import APIRouter, Depends, HTTPException
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
from app.services.trace_service import AgentTraceLogger, create_agent_run, update_agent_run
from app.services.risk_service import calculate_initial_risk
from app.core.config import settings
from app.core.errors import ChronosError
from app.workflows.intake import IntakeWorkflow
from app.workflows.runtime import WorkflowRunner

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
):
        
    agent_run_id = create_agent_run(user_id, "intake", {"text": request.text})
    if not agent_run_id:
        raise HTTPException(status_code=503, detail="Database not initialized.")

    trace_logger = AgentTraceLogger(user_id, agent_run_id)
    trace_logger.log(
        "intake_received",
        {"text_length": len(request.text)},
        status="started",
        explanation="Received brain dump for structured extraction",
    )

    try:
        workflow = IntakeWorkflow(
            gateway,
            WorkflowRunner(
                max_steps=settings.WORKFLOW_MAX_STEPS,
                timeout_seconds=settings.WORKFLOW_TIMEOUT_SECONDS,
                request_budget=settings.WORKFLOW_REQUEST_BUDGET,
            ),
        )
        result, workflow_traces = await workflow.extract(user_id=user_id, text=request.text)
        result.agent_run_id = uuid.UUID(agent_run_id)

        trace_logger.log(
            "drafts_prepared",
            {"count": len(result.drafts), "workflow_steps": len(workflow_traces), "provider": gateway.metadata().get("provider")},
            explanation="Prepared reviewable commitment drafts",
        )
        update_agent_run(agent_run_id, "completed", output_data=result.model_dump(mode="json"))
        return result
    except ChronosError as e:
        trace_logger.log(
            "extraction_failed",
            {"error_code": e.code},
            status="failed",
            explanation="Model extraction or validation failed",
        )
        update_agent_run(agent_run_id, "failed", error_message=e.code)
        raise


@router.post("/approve", response_model=ApproveCommitmentsResponse)
async def approve_intake(
    request: ApproveCommitmentsRequest,
    user_id: str = Depends(get_current_user),
    repositories: RepositorySet = Depends(get_repositories),
):
    if not request.approved_drafts:
        raise HTTPException(status_code=400, detail="No approved drafts provided.")

    agent_run_id = str(request.agent_run_id)
    trace_logger = AgentTraceLogger(user_id, agent_run_id)
    trace_logger.log(
        "approval_received",
        {"count": len(request.approved_drafts)},
        status="started",
        explanation="Received approved commitment drafts",
    )

    now = datetime.now(timezone.utc)
    commitments_inserted = 0

    try:
        for draft in request.approved_drafts:
            deadline_at = _parse_dt(draft.deadline_at)
            start_before_at = _parse_dt(draft.start_before_at)

            risk_score, risk_level, warnings = calculate_initial_risk(
                user_id=user_id,
                current_time=datetime.now(timezone.utc),
                deadline_at=deadline_at,
                estimated_minutes=draft.estimated_minutes,
                progress_percent=0.0,
                importance=draft.importance,
                flexibility=draft.flexibility,
                confidence_score=draft.confidence_score,
                start_before_at=start_before_at,
            )

            commitment_id = str(uuid.uuid4())
            comm_data = {
                "id": commitment_id,
                "user_id": user_id,
                "title": draft.title,
                "description": draft.done_condition,
                "type": _normalize_commitment_type(draft.type),
                "status": "active",
                "deadline_at": _json_dt(deadline_at),
                "start_before_at": _json_dt(start_before_at),
                "estimated_minutes": draft.estimated_minutes or 0,
                "actual_minutes": 0,
                "importance": draft.importance,
                "flexibility": draft.flexibility,
                "progress_percent": 0,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "confidence_score": draft.confidence_score,
            }
            repositories.commitments.create(user_id, comm_data)
            trace_logger.log(
                "commitments_persisted",
                {"id": commitment_id, "title": draft.title},
                explanation="Saved commitment to database",
            )
            trace_logger.log(
                "risk_initialized",
                {"id": commitment_id, "risk_level": risk_level, "risk_score": risk_score, "warnings": warnings},
                explanation="Initialized deterministic risk score",
            )

            if draft.tasks:
                task_rows = []
                for idx, t in enumerate(draft.tasks):
                    task_rows.append({
                        "id": str(uuid.uuid4()),
                        "commitment_id": commitment_id,
                        "user_id": user_id,
                        "title": t.title,
                        "next_action": getattr(t, "next_action", None),
                        "done_condition": getattr(t, "done_condition", None),
                        "status": "pending",
                        "estimated_minutes": t.estimated_minutes or 0,
                        "actual_minutes": 0,
                        "sequence_order": idx,
                    })
                repositories.commitments.create_tasks(user_id, task_rows)
                trace_logger.log(
                    "tasks_created",
                    {"commitment_id": commitment_id, "count": len(task_rows)},
                    explanation="Created child tasks",
                )

            is_major = (draft.estimated_minutes or 0) >= 240 or _normalize_commitment_type(draft.type) in {"hard_deadline", "soft_deadline"}
            checkpoints = [
                {"id": "capture", "status": "completed", "label": "Captured"},
                {"id": "clarify", "status": "completed", "label": "Clarified"},
                {"id": "next_action", "status": "pending", "label": "Next Action"},
            ]
            if is_major:
                checkpoints.extend([
                    {"id": "milestone", "status": "pending", "label": "Milestone"},
                    {"id": "feedback_gate", "status": "pending", "label": "Feedback Gate"},
                    {"id": "buffer", "status": "pending", "label": "Buffer Zone"},
                    {"id": "final_deadline", "status": "pending", "label": "Final Deadline"},
                ])
            else:
                checkpoints.extend([
                    {"id": "buffer", "status": "pending", "label": "Buffer Zone"},
                    {"id": "final_deadline", "status": "pending", "label": "Final Deadline"},
                ])
            checkpoints.append({"id": "reflection", "status": "pending", "label": "Reflection"})

            spine_data = {
                "id": str(uuid.uuid4()),
                "commitment_id": commitment_id,
                "user_id": user_id,
                "spine_json": checkpoints,
                "current_stage": "next_action",
            }
            repositories.commitments.create_time_spine(user_id, spine_data)
            trace_logger.log(
                "time_spines_created",
                {"commitment_id": commitment_id},
                explanation="Created basic Time Spine",
            )

            commitments_inserted += 1

        trace_logger.log(
            "approval_completed",
            {"count": commitments_inserted},
            explanation="Approval flow completed",
        )
        update_agent_run(agent_run_id, "completed")

        return ApproveCommitmentsResponse(
            status="success",
            count=commitments_inserted,
            message=f"Successfully approved {commitments_inserted} commitments.",
        )
    except Exception as e:
        trace_logger.log(
            "approval_failed",
            {"error_type": type(e).__name__},
            status="failed",
            explanation="Commitment approval persistence failed",
        )
        update_agent_run(agent_run_id, "failed", error_message=type(e).__name__)
        raise HTTPException(status_code=503, detail="ChronOS could not save the approved items.")
