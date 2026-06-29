from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.core.database import supabase_client
from app.services.google_calendar_service import sync_calendar_events, get_free_busy
from postgrest.exceptions import APIError

router = APIRouter()

class FreeBusyRequest(BaseModel):
    time_min: datetime
    time_max: datetime

@router.post("/sync")
def sync_calendar(user_id: str = Depends(get_current_user)):
    """Sync primary calendar events to ChronOS."""
    success = sync_calendar_events(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to sync calendar. Ensure Google Calendar is connected.")
    return {"success": True, "message": "Calendar synced successfully"}

@router.get("/events")
def get_events(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Retrieve synced calendar events."""
    try:
        now = datetime.now(timezone.utc)
        res = supabase_client.table("calendar_events").select("*").eq("user_id", user_id).gte("end_at", now.isoformat()).order("start_at").execute()
        return {"events": res.data if res.data else []}
    except APIError as e:
        raise HTTPException(status_code=500, detail="Failed to fetch calendar events from database")

@router.post("/free-busy")
def fetch_free_busy(req: FreeBusyRequest, user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Fetch free/busy slots from Google Calendar."""
    if not req.time_min.tzinfo:
        req.time_min = req.time_min.replace(tzinfo=timezone.utc)
    if not req.time_max.tzinfo:
        req.time_max = req.time_max.replace(tzinfo=timezone.utc)
        
    busy = get_free_busy(user_id, req.time_min, req.time_max)
    if busy is None:
        raise HTTPException(status_code=500, detail="Failed to fetch free/busy data. Ensure Google Calendar is connected.")
        
    return {"busy_blocks": busy}

@router.get("/capacity")
def get_capacity(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Return available focus capacity for today."""
    from app.services.capacity_service import get_layered_capacity
    now = datetime.now(timezone.utc)
    # End of today
    end_of_day = now.replace(hour=23, minute=59, second=59)
    capacity_data = get_layered_capacity(user_id, end_of_day, now)
    return capacity_data
