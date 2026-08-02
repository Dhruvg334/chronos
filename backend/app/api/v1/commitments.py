from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_repositories
from app.core.errors import ChronosError, ErrorCode
from app.repositories.protocols import RepositorySet
from app.schemas.commitments import CommitmentDetailResponse
from app.services.time_spine_service import get_time_spine_view

router = APIRouter()


@router.get("", response_model=list[dict])
async def get_commitments(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    rows = repositories.commitments.list_for_user(user_id)
    for row in rows:
        spine = repositories.commitments.get_time_spine(user_id, str(row["id"]))
        row["time_spines"] = [spine] if spine else []
    return rows


@router.get("/{commitment_id}", response_model=CommitmentDetailResponse)
async def get_commitment_detail(commitment_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    commitment = repositories.commitments.get_for_user(user_id, commitment_id)
    if not commitment:
        raise ChronosError(ErrorCode.VALIDATION, "Commitment not found.")
    time_spine = get_time_spine_view(commitment_id, user_id, repositories.commitments)
    return CommitmentDetailResponse(
        **commitment,
        tasks=repositories.commitments.list_tasks_for_user(user_id, commitment_id),
        time_spine_stages=time_spine["stages"],
        current_stage=time_spine["current_stage"],
        focus_blocks=[row for row in repositories.focus.list_for_user(user_id) if str(row.get("commitment_id")) == commitment_id],
        reflections=repositories.reflections.list_recent(user_id, commitment_id),
    )


@router.post("")
async def create_commitment():
    return {"message": "Use Inbox capture to create commitments."}


@router.patch("/{commitment_id}")
async def update_commitment(commitment_id: str):
    return {"message": f"Commitment updates are not enabled for {commitment_id}."}


@router.delete("/{commitment_id}")
async def delete_commitment(commitment_id: str):
    return {"message": f"Commitment deletion is not enabled for {commitment_id}."}
