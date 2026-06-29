import os
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from typing import Dict, Any

from app.api.dependencies import get_current_user
from app.services.google_oauth_service import (
    get_authorization_url,
    exchange_code_for_token,
    get_connection_status,
    disconnect
)

router = APIRouter()

@router.get("/auth/url")
def get_auth_url(user_id: str = Depends(get_current_user)) -> Dict[str, str]:
    """Return the Google OAuth authorization URL."""
    auth_url = get_authorization_url(user_id)
    return {"auth_url": auth_url}

@router.get("/auth/callback")
def auth_callback(code: str = Query(...), state: str = Query(...)):
    """
    Handle the OAuth callback from Google.
    Exchanges code for token and redirects to the frontend.
    The 'state' parameter contains the user_id.
    """
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    try:
        # State should be the user_id for this phase
        exchange_code_for_token(code=code, state=state)
        # Redirect back to command canvas with success
        return RedirectResponse(url=f"{frontend_url}/command?calendar_connected=true")
    except Exception as e:
        # Redirect back to command canvas with error
        return RedirectResponse(url=f"{frontend_url}/command?calendar_error=exchange_failed")

@router.get("/connection")
def connection_status(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Return the Google Calendar connection status (no secrets)."""
    return get_connection_status(user_id)

@router.post("/disconnect")
def disconnect_calendar(user_id: str = Depends(get_current_user)) -> Dict[str, bool]:
    """Disconnect Google Calendar and remove tokens."""
    disconnect(user_id)
    return {"success": True}
