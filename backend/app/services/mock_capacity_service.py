from datetime import datetime, timezone
from typing import Optional

# Mock Capacity assumptions
WORKDAY_START_HOUR = 9
WORKDAY_END_HOUR = 21
DEEP_WORK_RATIO = 0.45
DEFAULT_DAILY_FOCUS_MINUTES = 240
MINIMUM_BUFFER_MINUTES = 60

def get_available_capacity_until(deadline: Optional[datetime], current_time: datetime, tz_str: str = "UTC") -> int:
    """
    Returns a mocked estimate of available focus minutes between current_time and the deadline.
    If no deadline is provided, returns a generic large fallback.
    """
    if not deadline:
        return DEFAULT_DAILY_FOCUS_MINUTES * 7  # assume 7 days of default capacity

    # Calculate raw minutes difference
    delta = deadline - current_time
    total_minutes = int(delta.total_seconds() / 60)
    
    if total_minutes <= 0:
        return 0

    # In a real system, we'd subtract busy calendar blocks. 
    # Here, we just assume they have 240 minutes per day, pro-rated by how many days left, 
    # minus a minimum buffer, and only consider a fraction of time as deep work capable.
    
    # We will use a simplified calculation for mock capacity:
    # 1. Total available minutes = total_minutes
    # 2. Subtract MINIMUM_BUFFER_MINUTES
    usable_minutes = max(0, total_minutes - MINIMUM_BUFFER_MINUTES)
    
    # 3. Apply the DEEP_WORK_RATIO (45%) to available time
    estimated_capacity = int(usable_minutes * DEEP_WORK_RATIO)
    
    # Cap it to days * DEFAULT_DAILY_FOCUS_MINUTES for realism
    days = max(1, total_minutes // 1440)
    max_capacity = days * DEFAULT_DAILY_FOCUS_MINUTES
    
    return min(estimated_capacity, max_capacity)
