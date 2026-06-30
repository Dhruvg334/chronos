from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import os

from app.core.supabase import get_supabase_client

security = HTTPBearer(auto_error=False)

DEMO_USER_ID = "00000000-0000-0000-0000-000000000000"


def _dev_mode_enabled() -> bool:
    return os.environ.get("DEV_MODE", "false").lower() == "true"


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Return the authenticated Supabase user id.

    Local test/dev fallback is allowed only when DEV_MODE is explicitly enabled.
    Real bearer tokens are always verified with Supabase Auth.
    """
    dev_mode = _dev_mode_enabled()
    dev_user_id = os.environ.get("DEV_USER_ID", "").strip()

    if not credentials:
        if dev_mode and dev_user_id:
            return dev_user_id
        if dev_mode:
            return DEMO_USER_ID
        raise HTTPException(status_code=401, detail="Authentication required.")

    token = credentials.credentials.strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")

    if dev_mode and token == "mock_token":
        return dev_user_id or DEMO_USER_ID

    try:
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed.")

    user = getattr(user_response, "user", None)
    user_id = getattr(user, "id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication failed.")

    return user_id


def get_current_user(user_id: str = Depends(get_current_user_id)) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user_id
