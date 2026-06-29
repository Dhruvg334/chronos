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

def apply_skip_penalty(current_score: float) -> Tuple[float, str]:
    """Applies a flat penalty to risk when a block is skipped."""
    new_score = min(100.0, current_score + 15.0)
    return new_score, _get_level_from_score(new_score)

def apply_overrun_penalty(current_score: float, overrun_minutes: int) -> Tuple[float, str]:
    """Applies a penalty based on how many minutes over budget."""
    if overrun_minutes <= 0:
        return current_score, _get_level_from_score(current_score)
    penalty = min(25.0, (overrun_minutes / 30.0) * 5.0)
    new_score = min(100.0, current_score + penalty)
    return new_score, _get_level_from_score(new_score)

def recalculate_commitment_risk(commitment: dict, current_time: datetime, skip_penalty: bool = False) -> Tuple[float, str]:
    """
    Recalculates risk based on current DB state, applying penalties if necessary.
    """
    deadline_at_str = commitment.get("deadline_at")
    deadline_at = datetime.fromisoformat(deadline_at_str) if deadline_at_str else None
    if deadline_at and deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(tzinfo=timezone.utc)
        
    start_before_at_str = commitment.get("start_before_at")
    start_before_at = datetime.fromisoformat(start_before_at_str) if start_before_at_str else None
    if start_before_at and start_before_at.tzinfo is None:
        start_before_at = start_before_at.replace(tzinfo=timezone.utc)

    score, level, warnings = calculate_initial_risk(
        current_time=current_time,
        deadline_at=deadline_at,
        estimated_minutes=commitment.get("estimated_minutes"),
        progress_percent=float(commitment.get("progress_percent", 0.0)),
        importance=commitment.get("importance", 3),
        flexibility=commitment.get("flexibility", 3),
        confidence_score=commitment.get("confidence_score", 1.0),
        start_before_at=start_before_at
    )
    
    overrun = int(commitment.get("actual_minutes", 0)) - int(commitment.get("estimated_minutes", 0))
    if overrun > 0:
        score, level = apply_overrun_penalty(score, overrun)
        
    if skip_penalty:
        score, level = apply_skip_penalty(score)
        
    return score, level

def derive_next_best_action(commitments: List[dict]) -> Optional[dict]:
    """
    Determines the top priority commitment based on risk level and deadline.
    """
    if not commitments:
        return None
        
    # Sort by risk level weight, then deadline
    level_weights = {
        "rescue_required": 5,
        "critical": 4,
        "at_risk": 3,
        "watch": 2,
        "stable": 1
    }
    
    # We want max risk weight, min progress (if tied), min deadline
    def sort_key(c):
        w = level_weights.get(c.get("risk_level", "stable"), 1)
        prog = float(c.get("progress_percent", 0.0))
        deadline_str = c.get("deadline_at")
        deadline = datetime.fromisoformat(deadline_str).timestamp() if deadline_str else float('inf')
        return (-w, prog, deadline)
        
    sorted_comms = sorted(commitments, key=sort_key)
    return sorted_comms[0]
