from datetime import datetime, timedelta, timezone
import uuid

from fastapi import APIRouter, Depends, Header, Query, status

from app.api.dependencies import get_current_user, get_model_gateway, get_repositories
from app.core.config import settings
from app.core.observability import request_id_context
from app.models.gateway import ModelGateway
from app.repositories.protocols import RepositorySet
from app.schemas.adaptive import AdaptivePlanRequest, AdaptivePlanResponse, CandidatePlan
from app.schemas.planning_profile import PlanningProfile
from app.schemas.core import CreatePlanBlockRequest, PlanResponse
from app.services.core_journey import CoreJourneyService, rank_commitments
from app.workflows.adaptive_planning import AdaptivePlanningWorkflow
from app.workflows.runtime import WorkflowRunner

router = APIRouter()


@router.get("", response_model=PlanResponse)
async def get_plan(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    user_id: str = Depends(get_current_user),
    repositories: RepositorySet = Depends(get_repositories),
):
    start = start_at or datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = end_at or start + timedelta(days=1)
    if end <= start:
        from app.core.errors import ChronosError, ErrorCode
        raise ChronosError(ErrorCode.VALIDATION, "The plan range is invalid.")
    return CoreJourneyService(repositories).plan(user_id, start, end)


@router.post("/blocks", status_code=status.HTTP_201_CREATED)
async def create_plan_block(request: CreatePlanBlockRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    block = CoreJourneyService(repositories).create_plan_block(user_id, request.commitment_id, request.start_at, request.duration_minutes, request.title, request.block_type)
    return {"status": "created", "block": block}


@router.post("/adaptive", response_model=AdaptivePlanResponse)
async def recommend_adaptive_plan(
    request: AdaptivePlanRequest,
    user_id: str = Depends(get_current_user),
    repositories: RepositorySet = Depends(get_repositories),
    gateway: ModelGateway = Depends(get_model_gateway),
):
    workflow = AdaptivePlanningWorkflow(
        gateway,
        WorkflowRunner(
            max_steps=min(settings.WORKFLOW_MAX_STEPS, 4),
            timeout_seconds=settings.WORKFLOW_TIMEOUT_SECONDS,
            request_budget=min(settings.WORKFLOW_REQUEST_BUDGET, 3),
            trace_repository=repositories.traces,
        ),
        repositories,
    )
    return await workflow.recommend(
        user_id=user_id,
        start_at=request.start_at,
        end_at=request.end_at,
        request_id=request_id_context.get(),
    )


@router.post("/adaptive/{proposal_id}/approve")
async def approve_adaptive_plan(
    proposal_id: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user_id: str = Depends(get_current_user),
    repositories: RepositorySet = Depends(get_repositories),
):
    proposal = repositories.planning.get_proposal(user_id, proposal_id)
    if not proposal or proposal.get("action_type") != "commitment_reschedule":
        from app.core.errors import ChronosError, ErrorCode
        raise ChronosError(ErrorCode.VALIDATION, "Adaptive plan proposal not found.")
    if proposal.get("status") != "pending":
        from app.core.errors import ChronosError, ErrorCode
        raise ChronosError(ErrorCode.CONFLICT, "This adaptive plan proposal is no longer pending.")
    blocks = (proposal.get("payload_json") or {}).get("adaptive_plan", {}).get("blocks", [])
    candidate = CandidatePlan.model_validate((proposal.get("payload_json") or {}).get("adaptive_plan"))
    planning_range = (proposal.get("payload_json") or {}).get("planning_range")
    if planning_range and len(planning_range) == 2:
        range_start, range_end = datetime.fromisoformat(planning_range[0]), datetime.fromisoformat(planning_range[1])
    else:
        first = min(block.start_at for block in candidate.blocks)
        range_start = first.replace(hour=0, minute=0, second=0, microsecond=0)
        range_end = range_start + timedelta(days=1)
    service = CoreJourneyService(repositories)
    current_plan = service.plan(user_id, range_start, range_end)
    ranked = rank_commitments(repositories.commitments.list_for_user(user_id))
    validated = AdaptivePlanningWorkflow.validate_candidate(
        candidate,
        commitments={str(item["id"]): item for item in ranked},
        events=repositories.planning.list_calendar_events(user_id, range_start, range_end),
        existing_blocks=repositories.focus.list_for_user(user_id, range_start, range_end),
        profile=PlanningProfile.model_validate(repositories.planning_profiles.get(user_id)),
        range_start=range_start,
        range_end=range_end,
        remaining_capacity=current_plan.capacity.remaining_minutes,
    )
    if validated is None:
        from app.core.errors import ChronosError, ErrorCode
        raise ChronosError(ErrorCode.CONFLICT, "The proposed plan no longer fits your current calendar or availability.")
    block_ids = [str(uuid.uuid4()) for _ in blocks]
    return repositories.planning.approve_adaptive_plan(
        user_id,
        proposal_id,
        idempotency_key or f"adaptive-{proposal_id}",
        block_ids,
    )
