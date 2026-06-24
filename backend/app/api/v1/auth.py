from fastapi import APIRouter

router = APIRouter()

@router.get("/session")
async def get_session():
    return {
        "status": "mock_authenticated",
        "user_id": "00000000-0000-0000-0000-000000000000",
        "display_name": "ChronOS Demo User",
        "timezone": "UTC",
        "autonomy_level": "ask",
        "google_connected": False
    }

@router.post("/login")
async def login():
    return {"message": "Mock login successful"}

@router.post("/signup")
async def signup():
    return {"message": "Mock signup successful"}

@router.post("/logout")
async def logout():
    return {"message": "Mock logout successful"}
