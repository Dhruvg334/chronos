from fastapi import APIRouter
from typing import List

router = APIRouter()

@router.get("/")
async def get_commitments():
    return []

@router.post("/")
async def create_commitment():
    return {"message": "Mock commitment creation"}

@router.patch("/{commitment_id}")
async def update_commitment(commitment_id: str):
    return {"message": f"Mock commitment update for {commitment_id}"}

@router.delete("/{commitment_id}")
async def delete_commitment(commitment_id: str):
    return {"message": f"Mock commitment delete for {commitment_id}"}
