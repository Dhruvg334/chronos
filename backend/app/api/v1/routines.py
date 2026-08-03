from datetime import date

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_current_user, get_repositories
from app.repositories.protocols import RepositorySet
from app.schemas.planning_domains import RoutineOccurrenceUpdate, RoutinePatch, RoutineWrite
from app.services.planning_domains import PlanningDomainsService

router = APIRouter()


@router.get("")
async def list_routines(start: date | None = Query(default=None), user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return {"routines": PlanningDomainsService(repositories).list_routines(user_id, start=start)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_routine(request: RoutineWrite, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).create_routine(user_id, request.model_dump(mode="json"))


@router.put("/{routine_id}")
async def update_routine(routine_id: str, request: RoutinePatch, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).update_routine(user_id, routine_id, request.model_dump(mode="json", exclude_unset=True))


@router.post("/{routine_id}/occurrences")
async def record_occurrence(routine_id: str, request: RoutineOccurrenceUpdate, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).record_routine(user_id, routine_id, request.model_dump())
