from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.api.dependencies import get_repositories
from app.main import app
from tests.fakes import MemoryCommitments, MemoryFocus, MemoryReflections, repositories

client = TestClient(app)
USER = "00000000-0000-0000-0000-000000000001"


def commitment():
    return {"id": "c1", "user_id": USER, "title": "Authentication regression fix", "status": "active", "estimated_minutes": 60, "actual_minutes": 0, "progress_percent": 0, "risk_score": 40, "risk_level": "watch", "importance": 5, "flexibility": 1, "confidence_score": .9}


def test_focus_start_pause_resume_stuck_and_complete():
    commitments, focus, reflections = MemoryCommitments([commitment()]), MemoryFocus(), MemoryReflections()
    app.dependency_overrides[get_repositories] = lambda: repositories(commitments=commitments, focus=focus, reflections=reflections)
    started = client.post("/api/v1/focus-blocks/start", json={"commitment_id": "c1", "duration_minutes": 25})
    assert started.status_code == 200
    block_id = started.json()["session"]["id"]
    assert started.json()["session"]["planned_minutes"] == 25
    assert client.post(f"/api/v1/focus-blocks/{block_id}/pause").json()["session"]["status"] == "paused"
    assert client.post(f"/api/v1/focus-blocks/{block_id}/resume").json()["session"]["status"] == "active"
    options = client.post(f"/api/v1/focus-blocks/{block_id}/stuck").json()["options"]
    assert options == ["Define a smaller next step", "Identify missing information", "Switch to a short setup action", "Request a recovery suggestion"]
    completed = client.post(f"/api/v1/focus-blocks/{block_id}/complete", json={"actual_minutes": 20, "completion_status": "partial", "energy_level": 3, "progress_percent": 40})
    assert completed.status_code == 200
    assert completed.json()["reflection"]["energy_level"] == 3
    assert commitments.rows[0]["progress_percent"] == 40


def test_focus_stop_requires_reason_and_requests_reflection():
    now = datetime.now(timezone.utc)
    focus = MemoryFocus([{"id": "f1", "user_id": USER, "commitment_id": "c1", "title": "Fix", "start_at": now.isoformat(), "end_at": (now + timedelta(minutes=25)).isoformat(), "started_at": now.isoformat(), "status": "active"}])
    app.dependency_overrides[get_repositories] = lambda: repositories(commitments=MemoryCommitments([commitment()]), focus=focus)
    response = client.post("/api/v1/focus-blocks/f1/skip", json={"reason": "Missing test fixture"})
    assert response.status_code == 200
    assert response.json()["reflection_requested"] is True
    assert focus.rows[0]["stopped_reason"] == "Missing test fixture"
