from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.services.google_oauth_service import (
    disconnect,
    exchange_code_for_token,
    get_authorization_url,
    get_connection_status,
)

router = APIRouter()


def _frontend_redirect(query: str) -> RedirectResponse:
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    return RedirectResponse(url=f"{frontend_url}/command?{query}")


@router.get("/auth/url")
def get_auth_url(user_id: str = Depends(get_current_user)) -> Dict[str, str]:
    """Return the Google OAuth authorization URL."""
    auth_url = get_authorization_url(user_id)
    return {"auth_url": auth_url}


@router.get("/auth/callback")
def auth_callback(
    code: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    error: Optional[str] = Query(default=None),
):
    """Handle the OAuth callback from Google and redirect back to frontend safely."""
    if error:
        return _frontend_redirect("calendar_error=google_denied")
    if not code or not state:
        return _frontend_redirect("calendar_error=missing_oauth_params")

    try:
        exchange_code_for_token(code=code, state=state)
        return _frontend_redirect("calendar_connected=true")
    except ValueError:
        return _frontend_redirect("calendar_error=invalid_oauth_state")
    except Exception:
        return _frontend_redirect("calendar_error=exchange_failed")


@router.get("/connection")
def connection_status(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Return the Google Calendar connection status with no token material."""
    return get_connection_status(user_id)


@router.post("/disconnect")
def disconnect_calendar(user_id: str = Depends(get_current_user)) -> Dict[str, bool]:
    """Disconnect Google Calendar and remove Vault token material."""
    disconnect(user_id)
    return {"success": True}
