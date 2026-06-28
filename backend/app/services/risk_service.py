from datetime import datetime, timezone
from typing import Optional, Tuple, List
from app.services.mock_capacity_service import get_available_capacity_until

def calculate_initial_risk(
    current_time: datetime,
    deadline_at: Optional[datetime] = None,
    estimated_minutes: Optional[int] = None,
    progress_percent: float = 0.0,
    importance: int = 3,
    flexibility: int = 3,
    confidence_score: float = 1.0,
    start_before_at: Optional[datetime] = None,
    tz_str: str = "UTC"
) -> Tuple[float, str, List[str]]:
    """
    Calculates the deterministic risk score and level for a commitment.
    Returns (risk_score, risk_level, warnings).
    """
    warnings = []
    
    # Missing fields rules
    if not deadline_at or not estimated_minutes:
        if not deadline_at:
            warnings.append("Missing deadline_at. Defaulting risk to 'watch'.")
        if not estimated_minutes:
            warnings.append("Missing estimated_minutes. Defaulting risk to 'watch'.")
        return (40.0, "watch", warnings)
    
    # Time calculations
    delta = deadline_at - current_time
    minutes_until_deadline = int(delta.total_seconds() / 60)
    
    if minutes_until_deadline <= 0 and progress_percent < 100.0:
        warnings.append("Deadline has passed and commitment is incomplete.")
        return (100.0, "rescue_required", warnings)
        
    minutes_until_deadline = max(minutes_until_deadline, 0)
    
    # Derived values
    effort_remaining = estimated_minutes * (1 - (progress_percent / 100.0))
    urgency_ratio = effort_remaining / max(minutes_until_deadline, 60)
    importance_factor = importance / 5.0
    rigidity_factor = (6 - flexibility) / 5.0
    uncertainty_factor = 1 + (1 - confidence_score) * 0.25
    
    # Raw formula
    raw_score = (urgency_ratio * 55) + (importance_factor * 20) + (rigidity_factor * 15)
    risk_score = raw_score * uncertainty_factor
    risk_score = max(0.0, min(100.0, risk_score))
    
    # Determine level
    level = _get_level_from_score(risk_score)
    
    # Capacity check rule
    available_capacity = get_available_capacity_until(deadline_at, current_time, tz_str)
    if effort_remaining > available_capacity:
        warnings.append("Estimated effort exceeds available mock capacity before deadline.")
        level = _escalate_level(level)
        # Adjust score minimally to match level floor
        risk_score = max(risk_score, _get_floor_for_level(level))
        
    return (risk_score, level, warnings)

def _get_level_from_score(score: float) -> str:
    if score < 25:
        return "stable"
    elif score < 50:
        return "watch"
    elif score < 75:
        return "at_risk"
    elif score < 90:
        return "critical"
    else:
        return "rescue_required"

def _escalate_level(current_level: str) -> str:
    levels = ["stable", "watch", "at_risk", "critical", "rescue_required"]
    idx = levels.index(current_level)
    if idx < len(levels) - 1:
        return levels[idx + 1]
    return current_level

def _get_floor_for_level(level: str) -> float:
    floors = {
        "stable": 0.0,
        "watch": 25.0,
        "at_risk": 50.0,
        "critical": 75.0,
        "rescue_required": 90.0
    }
    return floors.get(level, 0.0)
