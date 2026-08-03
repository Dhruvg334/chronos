import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from googleapiclient.discovery import build
from postgrest.exceptions import APIError

from app.core.database import supabase_client
from app.services.google_oauth_service import get_valid_credentials

logger = logging.getLogger(__name__)

def sync_calendar_events(user_id: str, days_ahead: int = 14) -> bool:
    """
    Fetch events from Google Calendar and sync them to calendar_events.
    """
    creds = get_valid_credentials(user_id)
    if not creds:
        return False
        
    try:
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        
        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=max(1, min(days_ahead, 90)))).isoformat()
        
        # Get primary calendar events
        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=100,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        events = events_result.get("items", [])
        
        for event in events:
            # Skip full day events for now or handle them
            start = event["start"].get("dateTime")
            end = event["end"].get("dateTime")
            if not start or not end:
                continue
                
            payload = {
                "user_id": user_id,
                "google_event_id": event["id"],
                "title": event.get("summary", "Busy"),
                "start_at": start,
                "end_at": end,
                "source": "google",
                "is_chronos_created": False
            }
            
            supabase_client.table("calendar_events").upsert(payload, on_conflict="user_id,google_event_id").execute()
                
        # Update last_synced_at
        supabase_client.table("google_connections").update({
            "last_synced_at": now.isoformat()
        }).eq("user_id", user_id).execute()
        
        return True
    except Exception as exc:
        logger.warning("Google Calendar sync failed safely: %s", exc.__class__.__name__)
        return False

def get_free_busy(user_id: str, time_min: datetime, time_max: datetime) -> Optional[List[Dict[str, str]]]:
    """
    Query Google Calendar freeBusy endpoint.
    Returns a list of busy periods: [{"start": "...", "end": "..."}]
    """
    if time_max <= time_min:
        return None
    creds = get_valid_credentials(user_id)
    if not creds:
        return None
        
    try:
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        
        body = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "items": [{"id": "primary"}]
        }
        
        fb_result = service.freebusy().query(body=body).execute()
        calendars = fb_result.get("calendars", {})
        primary = calendars.get("primary", {})
        busy = primary.get("busy", [])
        
        return busy
    except Exception as exc:
        logger.warning("Google Calendar free/busy failed safely: %s", exc.__class__.__name__)
        return None
