from fastapi import APIRouter

router = APIRouter()

@router.get("/auth-url")
async def get_auth_url():
    return {"auth_url": "https://accounts.google.com/o/oauth2/v2/auth?mock=true"}

@router.get("/callback")
async def oauth_callback():
    return {"message": "Google OAuth connection complete (Mock)"}

@router.get("/events")
async def get_events():
    return []
