import pytest
from datetime import datetime, timezone, timedelta
from app.services.risk_service import calculate_initial_risk

def test_risk_missing_deadline():
    current_time = datetime.now(timezone.utc)
    score, level, warnings = calculate_initial_risk(
        user_id="test_user",
        current_time=current_time,
        deadline_at=None,
        estimated_minutes=120
    )
    assert level == "watch"
    assert any("Missing deadline_at" in w for w in warnings)

def test_risk_missing_effort():
    current_time = datetime.now(timezone.utc)
    score, level, warnings = calculate_initial_risk(
        user_id="test_user",
        current_time=current_time,
        deadline_at=current_time + timedelta(days=2),
        estimated_minutes=None
    )
    assert level == "watch"
    assert any("Missing estimated_minutes" in w for w in warnings)

def test_risk_overdue():
    current_time = datetime.now(timezone.utc)
    score, level, warnings = calculate_initial_risk(
        user_id="test_user",
        current_time=current_time,
        deadline_at=current_time - timedelta(days=1),
        estimated_minutes=120,
        progress_percent=50.0
    )
    assert level == "rescue_required"
    assert score == 100.0

def test_risk_stable():
    current_time = datetime.now(timezone.utc)
    score, level, warnings = calculate_initial_risk(
        user_id="test_user",
        current_time=current_time,
        deadline_at=current_time + timedelta(days=10),
        estimated_minutes=30, # Small effort, lots of time
        progress_percent=0.0,
        importance=1,
        flexibility=5,
        confidence_score=1.0
    )
    # Urgency ~0, Importance = 0.2*20=4, Rigidity = 1/5*15=3 -> score ~7
    assert level == "stable"

def test_risk_critical():
    current_time = datetime.now(timezone.utc)
    score, level, warnings = calculate_initial_risk(
        user_id="test_user",
        current_time=current_time,
        deadline_at=current_time + timedelta(minutes=120),
        estimated_minutes=120, # High effort, no time
        progress_percent=0.0,
        importance=5,
        flexibility=1,
        confidence_score=1.0
    )
    # Urgency ~2 (120/60) -> 2*55=110, Importance 1*20=20, Rigidity 1*15=15 -> >100
    assert level == "rescue_required" or level == "critical"
    
def test_risk_capacity_escalation():
    # If effort exceeds capacity
    current_time = datetime.now(timezone.utc)
    score, level, warnings = calculate_initial_risk(
        user_id="test_user",
        current_time=current_time,
        deadline_at=current_time + timedelta(hours=24), # 1 day
        estimated_minutes=1000, # Much more than 1 day's capacity (240)
        progress_percent=0.0,
        importance=3,
        flexibility=3
    )
    assert any("capacity" in w for w in warnings)

from app.services.risk_service import recalculate_commitment_risk, apply_skip_penalty, apply_overrun_penalty

def test_apply_skip_penalty():
    score, level = apply_skip_penalty(20.0) # stable
    assert score == 35.0
    assert level == "watch"

def test_apply_overrun_penalty():
    score, level = apply_overrun_penalty(20.0, 30) # 30 mins over = 5.0 penalty
    assert score == 25.0
    assert level == "watch"

def test_recalculate_commitment_risk():
    current_time = datetime.now(timezone.utc)
    commitment = {
        "estimated_minutes": 60,
        "actual_minutes": 90, # 30 mins overrun
        "progress_percent": 50.0,
        "deadline_at": (current_time + timedelta(hours=2)).isoformat(),
        "importance": 3,
        "flexibility": 3,
        "confidence_score": 1.0
    }
    
    score, level = recalculate_commitment_risk(commitment, current_time)
    
    # Overrun penalty should be applied
    # 30 mins over => 5.0 points.
    assert score > 0
    assert level in ["watch", "at_risk", "critical", "rescue_required"]
