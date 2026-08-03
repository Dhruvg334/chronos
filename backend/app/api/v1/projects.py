from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_repositories
from app.repositories.protocols import RepositorySet
from app.schemas.planning_domains import LinkWorkRequest, OutcomePatch, OutcomeWrite, ProjectPatch, ProjectWrite
from app.services.planning_domains import PlanningDomainsService

router = APIRouter()


@router.get("")
async def list_projects(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return {"projects": PlanningDomainsService(repositories).list_projects(user_id)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(request: ProjectWrite, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).create_project(user_id, request.model_dump(mode="json"))


@router.get("/{project_id}")
async def get_project(project_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).project_detail(user_id, project_id)


@router.put("/{project_id}")
async def update_project(project_id: str, request: ProjectPatch, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).update_project(user_id, project_id, request.model_dump(mode="json", exclude_unset=True))


@router.post("/{project_id}/archive")
async def archive_project(project_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).update_project(user_id, project_id, {"status": "archived"})


@router.post("/{project_id}/outcomes", status_code=status.HTTP_201_CREATED)
async def create_project_outcome(project_id: str, request: OutcomeWrite, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).create_outcome(user_id, {**request.model_dump(mode="json"), "project_id": project_id})


@router.post("/outcomes", status_code=status.HTTP_201_CREATED)
async def create_outcome(request: OutcomeWrite, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).create_outcome(user_id, request.model_dump(mode="json"))


@router.put("/outcomes/{outcome_id}")
async def update_outcome(outcome_id: str, request: OutcomePatch, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).update_outcome(user_id, outcome_id, request.model_dump(mode="json", exclude_unset=True))


@router.post("/outcomes/{outcome_id}/complete")
async def complete_outcome(outcome_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return PlanningDomainsService(repositories).update_outcome(user_id, outcome_id, {"status": "completed"})


@router.post("/outcomes/{outcome_id}/link")
async def link_outcome_work(outcome_id: str, request: LinkWorkRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    PlanningDomainsService(repositories).link_outcome_work(user_id, outcome_id, request.commitment_ids, request.task_ids)
    return {"status": "linked", "commitment_count": len(request.commitment_ids), "task_count": len(request.task_ids)}
