from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
import pytest

client = TestClient(app)

@patch("app.api.v1.calendar.sync_calendar_events")
def test_sync_calendar_success(mock_sync):
    mock_sync.return_value = True
    response = client.post("/api/v1/calendar/sync", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert response.json()["success"] is True

@patch("app.api.v1.calendar.sync_calendar_events")
def test_sync_calendar_failure(mock_sync):
    mock_sync.return_value = False
    response = client.post("/api/v1/calendar/sync", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 500

@patch("app.api.v1.calendar.supabase_client")
def test_get_events(mock_supabase):
    mock_execute = mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.execute
    mock_execute.return_value.data = [{"id": "1", "title": "Test Event"}]
    
    response = client.get("/api/v1/calendar/events", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert len(response.json()["events"]) == 1
    assert response.json()["events"][0]["title"] == "Test Event"

@patch("app.api.v1.calendar.get_free_busy")
def test_fetch_free_busy_success(mock_free_busy):
    mock_free_busy.return_value = [{"start": "2026-06-29T10:00:00Z", "end": "2026-06-29T11:00:00Z"}]
    response = client.post(
        "/api/v1/calendar/free-busy",
        headers={"Authorization": "Bearer mock_token"},
        json={"time_min": "2026-06-29T00:00:00Z", "time_max": "2026-06-29T23:59:59Z"}
    )
    assert response.status_code == 200
    assert len(response.json()["busy_blocks"]) == 1

@patch("app.api.v1.calendar.get_free_busy")
def test_fetch_free_busy_failure(mock_free_busy):
    mock_free_busy.return_value = None
    response = client.post(
        "/api/v1/calendar/free-busy",
        headers={"Authorization": "Bearer mock_token"},
        json={"time_min": "2026-06-29T00:00:00Z", "time_max": "2026-06-29T23:59:59Z"}
    )
    assert response.status_code == 500
