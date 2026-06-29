from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from app.services.mock_capacity_service import get_available_capacity_until as mock_capacity_until
from app.services.google_calendar_service import get_free_busy
from app.services.google_oauth_service import get_connection_status

MINIMUM_BUFFER_MINUTES = 60
DEEP_WORK_RATIO = 0.45
DEFAULT_DAILY_FOCUS_MINUTES = 240

def get_layered_capacity(user_id: str, deadline: Optional[datetime], current_time: datetime, tz_str: str = "UTC") -> Dict[str, Any]:
    """
    Layered capacity calculation.
    Uses Google Calendar free/busy if available, otherwise falls back to mock capacity.
    """
    if not deadline:
        # No deadline, return mock generic
        cap = mock_capacity_until(deadline, current_time, tz_str)
        return {
            "capacity_source": "mock",
            "available_minutes": cap,
            "focus_windows": [],
            "busy_blocks_count": 0,
            "fallback_reason": "no deadline provided"
        }
    
    # Try Google Calendar
    status = get_connection_status(user_id)
    if status.get("connected"):
        busy_blocks = get_free_busy(user_id, current_time, deadline)
        if busy_blocks is not None:
            # We have real busy blocks!
            delta = deadline - current_time
            total_minutes = int(delta.total_seconds() / 60)
            
            # Calculate busy minutes
            busy_minutes = 0
            for block in busy_blocks:
                b_start = datetime.fromisoformat(block["start"].replace('Z', '+00:00'))
                b_end = datetime.fromisoformat(block["end"].replace('Z', '+00:00'))
                
                # cap block within current_time and deadline
                effective_start = max(b_start, current_time)
                effective_end = min(b_end, deadline)
                if effective_end > effective_start:
                    busy_minutes += int((effective_end - effective_start).total_seconds() / 60)
            
            usable_minutes = max(0, total_minutes - busy_minutes - MINIMUM_BUFFER_MINUTES)
            estimated_capacity = int(usable_minutes * DEEP_WORK_RATIO)
            
            return {
                "capacity_source": "google_calendar",
                "available_minutes": estimated_capacity,
                "focus_windows": [], # Optional: We could invert busy blocks to find exact windows
                "busy_blocks_count": len(busy_blocks),
                "fallback_reason": None
            }
            
    # Fallback to mock
    cap = mock_capacity_until(deadline, current_time, tz_str)
    return {
        "capacity_source": "mock",
        "available_minutes": cap,
        "focus_windows": [],
        "busy_blocks_count": 0,
        "fallback_reason": "google connection not available or free_busy failed" if status.get("connected") else "not connected"
    }

def get_available_capacity_until(user_id: str, deadline: Optional[datetime], current_time: datetime, tz_str: str = "UTC") -> int:
    """Legacy wrapper for risk calculation which just needs the integer."""
    res = get_layered_capacity(user_id, deadline, current_time, tz_str)
    return res["available_minutes"]
