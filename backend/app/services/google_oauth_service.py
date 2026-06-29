import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from postgrest.exceptions import APIError

from app.core.database import supabase_client

logger = logging.getLogger(__name__)

def get_client_config() -> dict:
    return {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/google/auth/callback")],
        }
    }

def get_scopes() -> list:
    scopes_str = os.getenv("GOOGLE_SCOPES", "https://www.googleapis.com/auth/calendar.readonly")
    return [s.strip() for s in scopes_str.split(" ") if s.strip()]

def get_authorization_url(user_id: str) -> str:
    """Generate the Google OAuth authorization URL."""
    flow = Flow.from_client_config(
        get_client_config(),
        scopes=get_scopes(),
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
    )
    
    # We pass user_id as state to map the callback back to the user
    # In a production app, state should also contain a CSRF token
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=user_id
    )
    return auth_url

def exchange_code_for_token(code: str, state: str) -> None:
    """Exchange the authorization code for tokens and save to google_connections."""
    user_id = state
    flow = Flow.from_client_config(
        get_client_config(),
        scopes=get_scopes(),
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
    )
    
    flow.fetch_token(code=code)
    creds = flow.credentials

    # We need the user's email. We can get it from the userinfo endpoint, but we didn't request that scope.
    # We will just store a placeholder or try to extract from id_token if available.
    # For now, placeholder "connected@google.com" is enough unless we add email scope.
    google_email = "connected_calendar"

    # Upsert the connection using the secure RPC
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
            
        logger.info(f"Successfully connected Google Calendar for user {user_id}")
    except APIError as e:
        logger.error(f"Failed to save google connection: {e}")
        raise ValueError("Database error saving connection")

def get_connection_status(user_id: str) -> Dict[str, Any]:
    """Return safe connection status without leaking tokens."""
    try:
        res = supabase_client.table("google_connections").select("id, google_email, scopes, last_synced_at").eq("user_id", user_id).single().execute()
        if res.data:
            return {
                "connected": True,
                "email": res.data.get("google_email"),
                "scopes": res.data.get("scopes"),
                "last_synced_at": res.data.get("last_synced_at")
            }
    except APIError:
        pass
    
    return {
        "connected": False
    }

def disconnect(user_id: str) -> None:
    """Remove the Google connection for the user."""
    try:
        supabase_client.rpc("delete_google_connection", {"p_user_id": user_id}).execute()
    except APIError as e:
        logger.error(f"Failed to delete google connection: {e}")

def get_valid_credentials(user_id: str) -> Optional[Credentials]:
    """Retrieve and optionally refresh the credentials for a user."""
    try:
        res = supabase_client.rpc("get_decrypted_google_tokens", {"p_user_id": user_id}).execute()
        if not res.data or len(res.data) == 0:
            return None
            
        conn = res.data[0]
        creds = Credentials(
            token=conn["access_token"],
            refresh_token=conn.get("refresh_token"),
            token_uri=conn["token_uri"],
            client_id=conn["client_id"],
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            scopes=conn["scopes"]
        )
        
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Update DB with new access token
            rpc_payload = {
                "p_user_id": user_id,
                "p_google_email": "connected_calendar", # this might overwrite email if we had one, but we are just refreshing
                "p_access_token": creds.token,
                "p_refresh_token": "", # don't overwrite refresh token
                "p_token_uri": creds.token_uri,
                "p_client_id": creds.client_id,
                "p_scopes": conn["scopes"],
                "p_expires_at": creds.expiry.replace(tzinfo=timezone.utc).isoformat() if creds.expiry else None,
            }
            supabase_client.rpc("set_google_tokens", rpc_payload).execute()
            
        return creds
    except APIError as e:
        logger.error(f"Failed to retrieve credentials: {e}")
        return None
