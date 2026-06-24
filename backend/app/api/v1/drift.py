from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def log_drift():
    return {"message": "Mock drift event logged", "replan_proposed": False}
