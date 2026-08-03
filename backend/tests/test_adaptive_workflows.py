from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.api.dependencies import get_model_gateway, get_repositories
from app.main import app
from app.models.fake import FakeModelGateway
from app.schemas.adaptive import CandidatePlan, CandidatePlanBlock, PlanningModelOutput, RecoveryModelOutput, RecoveryOption
from tests.fakes import MemoryCommitments, MemoryFocus, MemoryPlanning, MemoryTraces, repositories


USER = "00000000-0000-0000-0000-000000000001"
client = TestClient(app)


def commitment(identifier="c1", **updates):
    return {"id": identifier, "user_id": USER, "title": "Authentication fix", "description": "Regression suite passes", "type": "hard_deadline", "status": "active", "estimated_minutes": 90, "actual_minutes": 0, "importance": 5, "flexibility": 1, "progress_percent": 0, "risk_score": 65, "risk_level": "at_risk", "confidence_score": .9, **updates}


def planning_range():
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    return start, start.replace(hour=18)


def test_adaptive_plan_rejects_invalid_candidate_and_waits_for_approval():
    start, end = planning_range()
    valid = CandidatePlan(label="Protect the fix", summary="One focused block.", blocks=[CandidatePlanBlock(commitment_id="c1", start_at=start + timedelta(hours=1), duration_minutes=60, rationale="Highest-risk executable outcome.")])
    invalid = CandidatePlan(label="Outside hours", summary="Invalid candidate.", blocks=[CandidatePlanBlock(commitment_id="c1", start_at=end + timedelta(hours=2), duration_minutes=60, rationale="Outside availability.")])
    model = FakeModelGateway(structured=PlanningModelOutput(diagnosis="The urgent fix needs protected time.", candidates=[invalid, valid]))
    store, focus, traces = MemoryPlanning(), MemoryFocus(), MemoryTraces()
    repos = repositories(commitments=MemoryCommitments([commitment()]), focus=focus, planning=store, traces=traces)
    app.dependency_overrides[get_model_gateway] = lambda: model
    app.dependency_overrides[get_repositories] = lambda: repos
    response = client.post("/api/v1/plan/adaptive", json={"start_at": start.isoformat(), "end_at": end.isoformat()})
    assert response.status_code == 200
    data = response.json()
    assert data["rejected_candidate_count"] == 1
    assert data["explanation"]["ai_used"] is True
    assert data["requires_approval"] is True
    assert store.proposals[0]["status"] == "pending" and focus.rows == []
    approved = client.post(f"/api/v1/plan/adaptive/{data['proposal_id']}/approve", headers={"Idempotency-Key": "adaptive-test-001"})
    assert approved.status_code == 200 and approved.json()["status"] == "approved"
    assert len(focus.rows) == 1


def test_adaptive_plan_rejects_dependency_blocked_work():
    start, end = planning_range()
    candidate = CandidatePlan(label="Blocked work", summary="Should fail.", blocks=[CandidatePlanBlock(commitment_id="c1", start_at=start + timedelta(hours=1), duration_minutes=30, rationale="Try blocked work.")])
    app.dependency_overrides[get_model_gateway] = lambda: FakeModelGateway(structured=PlanningModelOutput(diagnosis="Blocked.", candidates=[candidate]))
    app.dependency_overrides[get_repositories] = lambda: repositories(commitments=MemoryCommitments([commitment(status="blocked", type="waiting_on")]))
    response = client.post("/api/v1/plan/adaptive", json={"start_at": start.isoformat(), "end_at": end.isoformat()})
    assert response.status_code == 422
    assert "No proposed plan fit" in response.json()["error"]["message"]


def test_adaptive_recovery_uses_deterministic_diagnosis_and_limits_options():
    options = [
        RecoveryOption(action="protect_short_block", rationale="Reserve a small slot.", trade_off="Other work waits.", expected_impact="Restores momentum.", feasibility_reason="A slot should fit."),
        RecoveryOption(action="defer_lower_priority", rationale="Wait for the dependency.", trade_off="Delivery may move.", expected_impact="Avoids false execution.", feasibility_reason="Deferral is possible."),
    ]
    app.dependency_overrides[get_model_gateway] = lambda: FakeModelGateway(structured=RecoveryModelOutput(diagnosis="overload", options=options))
    planning = MemoryPlanning()
    app.dependency_overrides[get_repositories] = lambda: repositories(commitments=MemoryCommitments([commitment(status="blocked", type="waiting_on")]), planning=planning)
    response = client.post("/api/v1/rescue/c1/plan")
    assert response.status_code == 200
    data = response.json()
    assert data["diagnosis"] == "dependency_blocked"
    assert len(data["proposals"]) == 2
    first = data["proposals"][0]["payload_json"]
    assert first["feasible"] is False and first["required_approval"] is True
    denied = client.post(f"/api/v1/rescue/proposals/{data['proposals'][0]['id']}/approve")
    assert denied.status_code == 409


def test_plan_response_explains_deterministic_reasoning_without_hidden_trace():
    start, end = planning_range()
    app.dependency_overrides[get_repositories] = lambda: repositories(commitments=MemoryCommitments([commitment()]))
    data = client.get("/api/v1/plan", params={"start_at": start.isoformat(), "end_at": end.isoformat()}).json()
    assert data["explanation"]["ai_used"] is False
    assert data["explanation"]["requires_approval"] is True
    assert "risk" in data["explanation"]["next_action_reason"]
