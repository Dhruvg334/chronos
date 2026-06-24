from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def submit_reflection():
    return {"message": "Mock reflection logged successfully"}
