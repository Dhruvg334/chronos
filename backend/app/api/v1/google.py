from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_current_user, get_repositories
from app.core.config import settings
from app.repositories.protocols import RepositorySet
import uuid
from datetime import datetime, timezone
from app.services.google_oauth_service import (
    disconnect,
    exchange_code_for_token,
    get_authorization_url,
    get_connection_status,
    get_scopes,
)

router = APIRouter()


def _frontend_redirect(query: str) -> RedirectResponse:
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    return RedirectResponse(url=f"{frontend_url}/today?{query}")


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
    repositories: RepositorySet = Depends(get_repositories),
):
    """Handle the OAuth callback from Google and redirect back to frontend safely."""
    if error:
        return _frontend_redirect("calendar_error=google_denied")
    if not code or not state:
        return _frontend_redirect("calendar_error=missing_oauth_params")

    try:
        user_id = exchange_code_for_token(code=code, state=state)
        existing = repositories.integrations.get_connection(user_id, "google_calendar")
        payload = {"status": "connected", "granted_scopes": get_scopes(), "external_account_reference": "primary", "token_reference": "vault:google_calendar", "connected_at": datetime.now(timezone.utc).isoformat(), "last_error_at": None, "last_error_code": None, "sync_metadata": {"selected_resources": ["primary"]}}
        if existing: repositories.integrations.update_connection(user_id, existing["id"], payload)
        else: existing = repositories.integrations.create_connection(user_id, {"id": str(uuid.uuid4()), "provider": "google_calendar", **payload})
        repositories.integrations.append_audit(user_id, {"connection_id": existing["id"], "provider": "google_calendar", "event_type": "connection", "outcome": "connected", "safe_metadata": {}})
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
def disconnect_calendar(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)) -> Dict[str, bool]:
    """Disconnect Google Calendar and remove Vault token material."""
    disconnect(user_id)
    existing = repositories.integrations.get_connection(user_id, "google_calendar")
    if existing:
        repositories.integrations.update_connection(user_id, existing["id"], {"status": "revoked", "sync_cursor": None})
        repositories.integrations.append_audit(user_id, {"connection_id": existing["id"], "provider": "google_calendar", "event_type": "disconnection", "outcome": "revoked", "safe_metadata": {}})
    return {"success": True}
