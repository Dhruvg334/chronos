from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_repositories
from app.models.operations import AccountDeleteRequest, KnowledgeDeleteRequest
from app.repositories.protocols import RepositorySet
from app.services.data_lifecycle import DataLifecycleService
from app.services.readiness import detailed_operational_status

router = APIRouter()


@router.get("/status")
async def operational_status(user_id: str = Depends(get_current_user)):
    return await detailed_operational_status(user_id)


@router.get("/data/inventory")
def inventory(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return DataLifecycleService(repositories).inventory(user_id)


@router.get("/data/export")
def export(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return DataLifecycleService(repositories).export(user_id)


@router.post("/data/delete-account")
def delete_account(request: AccountDeleteRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return DataLifecycleService(repositories).delete_account(user_id, request.confirmation)


@router.post("/data/knowledge/{source_id}/delete")
def delete_source(source_id: str, request: KnowledgeDeleteRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return DataLifecycleService(repositories).delete_source(user_id, source_id)
