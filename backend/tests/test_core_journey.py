from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.api.dependencies import get_repositories
from app.main import app
from tests.fakes import MemoryCommitments, MemoryFocus, MemoryPlanning, repositories

client = TestClient(app)
USER = "00000000-0000-0000-0000-000000000001"


def item(identifier="c1", **overrides):
    return {"id": identifier, "user_id": USER, "title": "Authentication regression fix", "description": "Run the regression suite", "status": "active", "type": "hard_deadline", "estimated_minutes": 60, "actual_minutes": 0, "progress_percent": 0, "importance": 5, "flexibility": 1, "risk_level": "critical", "risk_score": 85, "confidence_score": .9, **overrides}


def test_today_returns_one_ranked_action_and_authoritative_strategy():
    app.dependency_overrides[get_repositories] = lambda: repositories(commitments=MemoryCommitments([item(), item("c2", title="Slides", risk_level="watch", importance=3)]))
    response = client.get("/api/v1/today")
    assert response.status_code == 200
    data = response.json()
    assert data["next_action"]["commitment_id"] == "c1"
    assert data["strategy_recommendation"]["strategy"] == "eisenhower_triage"
    assert data["strategy_recommendation"]["automatic_change"] is False
    assert len([data["strategy_recommendation"]]) == 1


def test_strategy_endpoint_covers_focus_interval_and_withholds_energy_without_evidence():
    app.dependency_overrides[get_repositories] = lambda: repositories()
    focus = client.post("/api/v1/today/strategy", json={"context": {"task_title": "Fix", "estimate_minutes": 60}}).json()
    assert focus["recommendation"]["strategy"] == "focus_interval"
    energy = client.post("/api/v1/today/strategy", json={"context": {"energy_samples": 1, "energy_confidence": .2}}).json()
    assert energy["recommendation"] is None


def test_plan_combines_events_blocks_unscheduled_capacity_and_buffers():
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0); end = start + timedelta(days=1)
    event = {"id": "e1", "user_id": USER, "title": "Team call", "start_at": (start + timedelta(hours=16)).isoformat(), "end_at": (start + timedelta(hours=17)).isoformat()}
    block = {"id": "b1", "user_id": USER, "commitment_id": "c2", "title": "Slides", "start_at": (start + timedelta(hours=11)).isoformat(), "end_at": (start + timedelta(hours=12)).isoformat(), "status": "scheduled"}
    app.dependency_overrides[get_repositories] = lambda: repositories(commitments=MemoryCommitments([item(), item("c2", title="Slides")]), focus=MemoryFocus([block]), planning=MemoryPlanning([event]))
    data = client.get("/api/v1/plan", params={"start_at": start.isoformat(), "end_at": end.isoformat()}).json()
    assert [row["kind"] for row in data["ordered_timeline"]] == ["focus_block", "calendar_event"]
    assert data["unscheduled_commitments"][0]["id"] == "c1"
    assert data["capacity"]["busy_minutes"] == 60
    assert data["capacity"]["planned_minutes"] == 60
    assert data["capacity"]["buffer_minutes"] == 10


def test_plan_block_creation_succeeds_when_free_and_rejects_overlap():
    start = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
    commitments = MemoryCommitments([item()]); focus = MemoryFocus(); planning = MemoryPlanning()
    app.dependency_overrides[get_repositories] = lambda: repositories(commitments=commitments, focus=focus, planning=planning)
    payload = {"commitment_id": "c1", "start_at": start.isoformat(), "duration_minutes": 60}
    created = client.post("/api/v1/plan/blocks", json=payload)
    assert created.status_code == 201
    conflict = client.post("/api/v1/plan/blocks", json=payload)
    assert conflict.status_code == 409
    assert "overlaps" in conflict.json()["error"]["message"]
