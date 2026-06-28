from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.database import supabase_client
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/")
async def get_commitments(user_id: str = Depends(get_current_user)):
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    res = supabase_client.table("commitments").select("*, time_spines(*)").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data

@router.post("/")
async def create_commitment():
    return {"message": "Mock commitment creation"}

@router.patch("/{commitment_id}")
async def update_commitment(commitment_id: str):
    return {"message": f"Mock commitment update for {commitment_id}"}

@router.delete("/{commitment_id}")
async def delete_commitment(commitment_id: str):
    return {"message": f"Mock commitment delete for {commitment_id}"}
