from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.database import supabase_client
from app.api.dependencies import get_current_user

from app.schemas.commitments import CommitmentDetailResponse
from app.services.time_spine_service import get_time_spine_view

router = APIRouter()

@router.get("", response_model=list[dict])
async def get_commitments(user_id: str = Depends(get_current_user)):
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    res = supabase_client.table("commitments").select("*, time_spines(*)").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data

@router.get("/{commitment_id}", response_model=CommitmentDetailResponse)
async def get_commitment_detail(commitment_id: str, user_id: str = Depends(get_current_user)):
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized")

    # Fetch commitment
    comm_res = supabase_client.table("commitments").select("*").eq("id", commitment_id).eq("user_id", user_id).single().execute()
    if not comm_res.data:
        raise HTTPException(status_code=404, detail="Commitment not found")
    
    comm = comm_res.data

    # Fetch tasks
    tasks_res = supabase_client.table("tasks").select("*").eq("commitment_id", commitment_id).order("sequence_order").execute()
    
    # Fetch focus blocks
    blocks_res = supabase_client.table("focus_blocks").select("*").eq("commitment_id", commitment_id).order("created_at", desc=True).execute()
    
    # Fetch reflections
    refl_res = supabase_client.table("reflections").select("*").eq("commitment_id", commitment_id).order("created_at", desc=True).limit(5).execute()

    # Time Spine
    time_spine = get_time_spine_view(commitment_id, user_id)

    return CommitmentDetailResponse(
        **comm,
        tasks=tasks_res.data or [],
        time_spine_stages=time_spine.get("stages", []),
        current_stage=time_spine.get("current_stage"),
        focus_blocks=blocks_res.data or [],
        reflections=refl_res.data or []
    )

@router.post("")
async def create_commitment():
    return {"message": "Mock commitment creation"}

@router.patch("/{commitment_id}")
async def update_commitment(commitment_id: str):
    return {"message": f"Mock commitment update for {commitment_id}"}

@router.delete("/{commitment_id}")
async def delete_commitment(commitment_id: str):
    return {"message": f"Mock commitment delete for {commitment_id}"}
