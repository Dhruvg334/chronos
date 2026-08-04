from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_repositories
from app.repositories.protocols import RepositorySet

router = APIRouter()


@router.get("/{run_id}/trace")
def workflow_trace(run_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return {"events": repositories.traces.list_events(user_id, run_id)}
