import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from postgrest.exceptions import APIError

from app.core.config import settings
from app.core.database import supabase_client

logger = logging.getLogger(__name__)

_STATE_MAX_AGE_SECONDS = 10 * 60


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("utf-8"))


def _state_secret() -> str:
    """Return a backend-only secret used to sign OAuth state."""
    secret = (
        settings.GOOGLE_OAUTH_STATE_SECRET
        or settings.GOOGLE_CLIENT_SECRET
        or settings.SUPABASE_SERVICE_ROLE_KEY
    )
    if not secret:
        raise ValueError("Google OAuth state signing secret is not configured")
    return secret


def create_oauth_state(user_id: str) -> str:
    """Create a signed, short-lived OAuth state payload.

    The callback cannot depend on browser auth headers, so the user id is carried
    inside a signed payload. This protects against trivial user-id substitution
    and CSRF-style callback injection.
    """
    payload = {
        "uid": user_id,
        "nonce": secrets.token_urlsafe(16),
        "ts": int(time.time()),
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(_state_secret().encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    return f"{payload_b64}.{_b64url_encode(sig)}"


def validate_oauth_state(state: str) -> str:
    """Validate OAuth state and return the embedded user id."""
    try:
        payload_b64, sig_b64 = state.split(".", 1)
        expected = hmac.new(_state_secret().encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
        actual = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected, actual):
            raise ValueError("Invalid OAuth state signature")
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        ts = int(payload.get("ts", 0))
        if int(time.time()) - ts > _STATE_MAX_AGE_SECONDS:
            raise ValueError("OAuth state expired")
        user_id = payload.get("uid")
        if not user_id:
            raise ValueError("OAuth state missing user id")
        return str(user_id)
    except Exception as exc:
        logger.warning("Rejected invalid Google OAuth state: %s", exc)
        raise ValueError("Invalid OAuth state") from exc


def get_client_config() -> dict:
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID or os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": settings.GOOGLE_CLIENT_SECRET or os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }


def get_scopes() -> list[str]:
    scopes_str = settings.GOOGLE_SCOPES or os.getenv("GOOGLE_SCOPES", "https://www.googleapis.com/auth/calendar.readonly")
    return [s.strip() for s in scopes_str.split(" ") if s.strip()]


def get_authorization_url(user_id: str) -> str:
    """Generate the Google OAuth authorization URL with signed state."""
    flow = Flow.from_client_config(
        get_client_config(),
        scopes=get_scopes(),
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=create_oauth_state(user_id),
    )
    return auth_url


def exchange_code_for_token(code: str, state: str) -> None:
    """Exchange the authorization code for tokens and save them through Vault RPC."""
    user_id = validate_oauth_state(state)
    flow = Flow.from_client_config(
        get_client_config(),
        scopes=get_scopes(),
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )

    flow.fetch_token(code=code)
    creds = flow.credentials
    google_email = "connected_calendar"

    try:
        rpc_payload = {
            "p_user_id": user_id,
            "p_google_email": google_email,
            "p_access_token": creds.token,
            "p_refresh_token": creds.refresh_token or "",
            "p_token_uri": creds.token_uri,
            "p_client_id": creds.client_id,
            "p_scopes": get_scopes(),
            "p_expires_at": creds.expiry.replace(tzinfo=timezone.utc).isoformat() if creds.expiry else None,
        }
        supabase_client.rpc("set_google_tokens", rpc_payload).execute()
        logger.info("Successfully connected Google Calendar for user %s", user_id)
    except APIError as e:
        logger.error("Failed to save google connection metadata")
        raise ValueError("Database error saving connection") from e


def get_connection_status(user_id: str) -> Dict[str, Any]:
    """Return safe connection status without leaking tokens or Vault IDs."""
    if supabase_client is None:
        return {"connected": False}

    try:
        res = (
            supabase_client.table("google_connections")
            .select("id, google_email, scopes, last_synced_at, expires_at")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if res.data:
            return {
                "connected": True,
                "email": res.data.get("google_email"),
                "scopes": res.data.get("scopes"),
                "last_synced_at": res.data.get("last_synced_at"),
                "token_expires_at": res.data.get("expires_at"),
            }
    except (APIError, AttributeError):
        pass

    return {"connected": False}


def disconnect(user_id: str) -> None:
    """Remove the Google connection and Vault material for the user."""
    if supabase_client is None:
        return

    try:
        supabase_client.rpc("delete_google_connection", {"p_user_id": user_id}).execute()
    except APIError as e:
        logger.error("Failed to delete google connection metadata")


def get_valid_credentials(user_id: str) -> Optional[Credentials]:
    """Retrieve and optionally refresh the credentials for a user."""
    if supabase_client is None:
        return None

    try:
        res = supabase_client.rpc("get_decrypted_google_tokens", {"p_user_id": user_id}).execute()
        if not res.data:
            return None

        conn = res.data[0]
        creds = Credentials(
            token=conn["access_token"],
            refresh_token=conn.get("refresh_token"),
            token_uri=conn["token_uri"],
            client_id=conn["client_id"],
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=conn["scopes"],
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            rpc_payload = {
                "p_user_id": user_id,
                "p_google_email": "connected_calendar",
                "p_access_token": creds.token,
                "p_refresh_token": "",  # Preserve existing refresh token.
                "p_token_uri": creds.token_uri,
                "p_client_id": creds.client_id,
                "p_scopes": conn["scopes"],
                "p_expires_at": creds.expiry.replace(tzinfo=timezone.utc).isoformat() if creds.expiry else None,
            }
            supabase_client.rpc("set_google_tokens", rpc_payload).execute()

        return creds
    except APIError as e:
        logger.error("Failed to retrieve Google credentials")
        return None
    except Exception as exc:
        logger.error("Google credential refresh failed safely: %s", exc.__class__.__name__)
        return None
