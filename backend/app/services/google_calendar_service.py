import logging
from datetime import datetime, timezone
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
        service = build("calendar", "v3", credentials=creds)
        
        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        
        # Get primary calendar events
        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
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
            
            # Upsert using compound key (requires supabase match or handling)
            # Supabase doesn't natively support ON CONFLICT easily via postgrest without a specific RPC
            # We'll check if it exists first
            res = supabase_client.table("calendar_events").select("id").eq("user_id", user_id).eq("google_event_id", event["id"]).execute()
            
            if res.data:
                supabase_client.table("calendar_events").update(payload).eq("id", res.data[0]["id"]).execute()
            else:
                supabase_client.table("calendar_events").insert(payload).execute()
                
        # Update last_synced_at
        supabase_client.table("google_connections").update({
            "last_synced_at": now.isoformat()
        }).eq("user_id", user_id).execute()
        
        return True
    except Exception as e:
        logger.error(f"Failed to sync calendar for user {user_id}: {e}")
        return False

def get_free_busy(user_id: str, time_min: datetime, time_max: datetime) -> Optional[List[Dict[str, str]]]:
    """
    Query Google Calendar freeBusy endpoint.
    Returns a list of busy periods: [{"start": "...", "end": "..."}]
    """
    creds = get_valid_credentials(user_id)
    if not creds:
        return None
        
    try:
        service = build("calendar", "v3", credentials=creds)
        
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
    except Exception as e:
        logger.error(f"Failed to fetch free/busy for user {user_id}: {e}")
        return None
