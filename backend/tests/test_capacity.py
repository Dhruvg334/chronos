from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from app.services.capacity_service import get_layered_capacity

@patch("app.services.capacity_service.get_connection_status")
def test_capacity_fallback_not_connected(mock_status):
    mock_status.return_value = {"connected": False}
    current = datetime.now(timezone.utc)
    deadline = current + timedelta(days=1)
    
    res = get_layered_capacity("user1", deadline, current)
    assert res["capacity_source"] == "mock"
    assert res["available_minutes"] > 0
    assert "not connected" in res["fallback_reason"]

@patch("app.services.capacity_service.get_connection_status")
@patch("app.services.capacity_service.get_free_busy")
def test_capacity_google_connected_success(mock_free_busy, mock_status):
    mock_status.return_value = {"connected": True}
    current = datetime.now(timezone.utc)
    deadline = current + timedelta(hours=5)
    
    # Mock one busy block of 1 hour
    mock_free_busy.return_value = [{
        "start": (current + timedelta(hours=1)).isoformat(),
        "end": (current + timedelta(hours=2)).isoformat()
    }]
    
    res = get_layered_capacity("user1", deadline, current)
    assert res["capacity_source"] == "google_calendar"
    assert res["busy_blocks_count"] == 1
    # Out of 5 hours (300 mins), minus buffer (60 mins), minus busy (60 mins) = 180 usable
    # 180 * 0.45 = 81 estimated focus minutes
    assert res["available_minutes"] == 81

@patch("app.services.capacity_service.get_connection_status")
@patch("app.services.capacity_service.get_free_busy")
def test_capacity_google_connected_fail(mock_free_busy, mock_status):
    mock_status.return_value = {"connected": True}
    current = datetime.now(timezone.utc)
    deadline = current + timedelta(hours=5)
    
    # API fails
    mock_free_busy.return_value = None
    
    res = get_layered_capacity("user1", deadline, current)
    assert res["capacity_source"] == "mock"
    assert "failed" in res["fallback_reason"]
