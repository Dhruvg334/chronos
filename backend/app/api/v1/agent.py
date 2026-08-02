from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_repositories
from app.repositories.protocols import RepositorySet

router = APIRouter()


@router.get("/runs/{agent_run_id}/trace")
async def get_agent_traces(agent_run_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return {"events": repositories.traces.list_events(user_id, agent_run_id)}


@router.post("/proposed/{action_id}/approve")
async def approve_proposed_action(action_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    proposal = repositories.planning.get_proposal(user_id, action_id)
    if proposal:
        repositories.planning.update_proposal(user_id, action_id, {"status": "approved"})
    return {"status": "approved", "action_id": action_id}


@router.post("/proposed/{action_id}/reject")
async def reject_proposed_action(action_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    proposal = repositories.planning.get_proposal(user_id, action_id)
    if proposal:
        repositories.planning.update_proposal(user_id, action_id, {"status": "rejected"})
    return {"status": "rejected", "action_id": action_id}
