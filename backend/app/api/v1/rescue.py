from fastapi import APIRouter

router = APIRouter()

@router.post("/activate")
async def activate_rescue():
    return {"message": "Mock rescue mode activated", "mvcp_checklist": []}
