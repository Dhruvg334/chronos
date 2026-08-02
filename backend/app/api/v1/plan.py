from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_current_user, get_repositories
from app.repositories.protocols import RepositorySet
from app.schemas.core import CreatePlanBlockRequest, PlanResponse
from app.services.core_journey import CoreJourneyService

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
