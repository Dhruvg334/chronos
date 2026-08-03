from datetime import date, timedelta

from fastapi import APIRouter, Depends, Header, Query

from app.api.dependencies import get_current_user, get_repositories
from app.repositories.protocols import RepositorySet
from app.schemas.planning_domains import WeeklyProposalEdit
from app.services.planning_domains import PlanningDomainsService

router = APIRouter()


def _monday(value: date | None) -> date:
    current = value or date.today()
    return current - timedelta(days=current.weekday())


@router.get("")
async def get_week(week_start: date | None = Query(default=None), user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).weekly_view(user_id, _monday(week_start))


@router.post("/proposals")
async def generate_proposal(week_start: date | None = Query(default=None), user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).generate_weekly_proposal(user_id, _monday(week_start))


@router.put("/proposals/{plan_id}")
async def edit_proposal(plan_id: str, request: WeeklyProposalEdit, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).edit_weekly_proposal(user_id, plan_id, request.blocks)


@router.post("/proposals/{plan_id}/approve")
async def approve_proposal(plan_id: str, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).approve_weekly_proposal(user_id, plan_id, idempotency_key or f"weekly-{plan_id}")


@router.post("/proposals/{plan_id}/reject")
async def reject_proposal(plan_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).reject_weekly_proposal(user_id, plan_id)
