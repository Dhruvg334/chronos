from fastapi import Depends, HTTPException
import os

# Temporary dev-auth dependency until Supabase JWT verification is implemented.
# Server-side code owns the user context; the frontend must never send user_id.
DEMO_USER_ID = "00000000-0000-0000-0000-000000000000"

def get_current_user_id() -> str:
    dev_user_id = os.environ.get("DEV_USER_ID", DEMO_USER_ID).strip()
    return dev_user_id or DEMO_USER_ID

def get_current_user(user_id: str = Depends(get_current_user_id)) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id
