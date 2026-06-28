from fastapi import Depends, HTTPException, Header, Request
from typing import Optional
import os

# Dev Auth mock
# This is a temporary dependency to simulate authentication until Supabase JWT auth middleware is fully implemented.
def get_current_user_id() -> str:
    # In a real environment, we'd parse the Authorization header JWT
    # For dev purposes, we look for a DEV_USER_ID env variable or default to a mock ID
    dev_user_id = os.environ.get("DEV_USER_ID")
    if not dev_user_id:
        # Fallback to User A's ID from DB_VERIFICATION.md mock data
        dev_user_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        
    return dev_user_id

def get_current_user(user_id: str = Depends(get_current_user_id)) -> str:
    """
    Dependency that returns the verified user_id.
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id
