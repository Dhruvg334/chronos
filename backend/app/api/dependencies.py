from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import jwt
from app.core.supabase import get_supabase_client

security = HTTPBearer(auto_error=False)

DEMO_USER_ID = "00000000-0000-0000-0000-000000000000"

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    # Allow DEV fallback if enabled (useful for backend tests without real tokens)
    dev_user_id = os.environ.get("DEV_USER_ID", "").strip()
    dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"
    
    if dev_mode and dev_user_id:
        return dev_user_id

    if not credentials:
        # If no credentials and we are in dev mode, maybe fallback to demo user?
        # Let's enforce credentials unless explicitly bypassed.
        if dev_mode:
            return DEMO_USER_ID
        raise HTTPException(status_code=401, detail="Not authenticated. Missing Bearer Token.")

    token = credentials.credentials
    
    # Fast path for tests sending mock_token
    if dev_mode and token == "mock_token":
        return DEMO_USER_ID

    try:
        # Validate JWT structure and get the unverified payload first (Supabase uses HS256 with JWT Secret)
        # The easiest way to verify the token without manually handling the secret is to use get_user
        supabase = get_supabase_client()
        # get_user validates the JWT against GoTrue server.
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token or user not found.")
            
        return user_response.user.id
        
    except Exception as e:
        # Fallback to local JWT decode if get_user fails due to networking? No, strict verification.
        # But wait, does the service role client support get_user(jwt) ? Yes, in python client: supabase.auth.get_user(jwt)
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

def get_current_user(user_id: str = Depends(get_current_user_id)) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id
