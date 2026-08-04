from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header

from app.api.dependencies import get_current_user, get_model_gateway, get_repositories
from app.core.config import settings
from app.core.errors import ChronosError, ErrorCode
from app.core.observability import request_id_context
from app.models.gateway import ModelGateway
from app.repositories.protocols import RepositorySet
from app.schemas.personalization import RecoveryChoiceCreate
from app.api.v1.recommendations import concise_context
from app.services.core_journey import rank_commitments
from app.workflows.adaptive_recovery import AdaptiveRecoveryWorkflow
from app.workflows.runtime import WorkflowRunner

router = APIRouter()


@router.get("/candidates")
def get_rescue_candidates(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)) -> dict[str, Any]:
    rows = rank_commitments(repositories.commitments.list_for_user(user_id))
    return {"candidates": [{**row, "_rescue_reason": "The current risk and remaining work need a more credible plan."} for row in rows if row.get("risk_level") in {"at_risk", "critical", "rescue_required"}]}


@router.post("/{commitment_id}/plan")
async def generate_rescue_plan(
    commitment_id: str,
    user_id: str = Depends(get_current_user),
    repositories: RepositorySet = Depends(get_repositories),
    gateway: ModelGateway = Depends(get_model_gateway),
) -> dict[str, Any]:
    return (await AdaptiveRecoveryWorkflow(
        gateway,
        WorkflowRunner(
            max_steps=min(settings.WORKFLOW_MAX_STEPS, 4),
            timeout_seconds=settings.WORKFLOW_TIMEOUT_SECONDS,
            request_budget=min(settings.WORKFLOW_REQUEST_BUDGET, 3),
            trace_repository=repositories.traces,
        ),
        repositories,
    ).recommend(user_id=user_id, commitment_id=commitment_id, request_id=request_id_context.get())).model_dump(mode="json")


@router.get("/plans")
def get_rescue_plans(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)) -> dict[str, Any]:
    return {"proposals": [row for row in repositories.planning.list_pending(user_id) if row.get("action_type") == "commitment_rescue"]}


def _pending(repositories: RepositorySet, user_id: str, proposal_id: str) -> dict[str, Any]:
    proposal = repositories.planning.get_proposal(user_id, proposal_id)
    if not proposal or proposal.get("action_type") != "commitment_rescue":
        raise ChronosError(ErrorCode.VALIDATION, "Recovery proposal not found.")
    if proposal.get("status") != "pending":
        raise ChronosError(ErrorCode.CONFLICT, "This recovery proposal is no longer pending.")
    return proposal


@router.post("/proposals/{proposal_id}/approve")
def approve_rescue_proposal(proposal_id: str, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)) -> dict[str, Any]:
    proposal = _pending(repositories, user_id, proposal_id)
    payload = proposal.get("payload_json") or {}
    if payload.get("feasible") is False:
        raise ChronosError(ErrorCode.CONFLICT, str(payload.get("feasibility_reason") or "This recovery option is not currently feasible."))
    focus_block_id = str(uuid.uuid4()) if payload.get("rescue_action_type") == "create_rescue_focus_block" else None
    return repositories.planning.approve_recovery(user_id, proposal_id, idempotency_key or f"recovery-{proposal_id}", focus_block_id)


@router.post("/proposals/{proposal_id}/reject")
def reject_rescue_proposal(proposal_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)) -> dict[str, Any]:
    _pending(repositories, user_id, proposal_id)
    repositories.planning.update_proposal(user_id, proposal_id, {"status": "rejected"})
    return {"status": "rejected"}


@router.post("/choices")
def record_recovery_choice(request: RecoveryChoiceCreate, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)) -> dict[str, Any]:
    row = repositories.feedback.create(user_id, {
        "id": str(uuid.uuid4()),
        "recommendation_type": "recovery",
        "recommendation_key": request.recommendation_key,
        "context_summary": concise_context({"surface": "recovery", "failure_mode": request.failure_mode, "option_id": request.option_id}),
        "user_action": request.choice,
        "reason_category": request.reason_category,
    })
    return {"id": row["id"], "status": "recorded", "plan_changed": False}
