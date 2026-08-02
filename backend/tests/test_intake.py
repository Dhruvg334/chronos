from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import get_model_gateway, get_repositories
from app.main import app
from app.models.fake import FakeModelGateway
from app.schemas.intake import IntakeResponse
from tests.fakes import MemoryCommitments, MemoryTraces, repositories

client = TestClient(app)


def test_intake_process_uses_injected_runtime_and_trace_repository():
    run_id = str(uuid4())
    traces = MemoryTraces()
    gateway = FakeModelGateway(structured=IntakeResponse(agent_run_id=run_id, drafts=[], questions=[]))
    app.dependency_overrides[get_model_gateway] = lambda: gateway
    app.dependency_overrides[get_repositories] = lambda: repositories(traces=traces)
    response = client.post("/api/v1/ai/intake", json={"text": "Finish the report tomorrow"})
    assert response.status_code == 200
    assert response.json()["agent_run_id"] in traces.runs
    assert traces.runs[response.json()["agent_run_id"]]["status"] == "completed"
    assert traces.events[0]["step_name"] == "extract_commitments"


def test_approve_empty():
    app.dependency_overrides[get_repositories] = lambda: repositories()
    response = client.post("/api/v1/ai/intake/approve", json={"agent_run_id": str(uuid4()), "approved_drafts": []})
    assert response.status_code == 400


def test_approve_success_persists_only_reviewed_drafts():
    run_id = str(uuid4())
    commitments, traces = MemoryCommitments(), MemoryTraces()
    traces.create_run("00000000-0000-0000-0000-000000000001", "intake", {}, workflow_id=run_id)
    app.dependency_overrides[get_repositories] = lambda: repositories(commitments=commitments, traces=traces)
    draft = {"title": "Do a thing", "type": "task", "estimated_minutes": 30, "importance": 3, "flexibility": 3, "confidence_score": 0.9, "tasks": [], "missing_fields": []}
    response = client.post("/api/v1/ai/intake/approve", json={"agent_run_id": run_id, "approved_drafts": [draft]})
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert len(commitments.rows) == 1
    assert traces.runs[run_id]["status"] == "completed"


def test_manual_capture_keeps_commitments_separate_and_uncertainty_visible():
    text = "I need to finish the authentication regression fix before tomorrow afternoon, prepare slides for Monday, attend a team call at 4 PM, and submit my database assignment by Tuesday morning. The auth fix needs about an hour, but I am unsure how long the slides will take."
    structured = IntakeResponse.model_validate({
        "agent_run_id": str(uuid4()),
        "drafts": [
            {"title": "Authentication regression fix", "type": "hard_deadline", "estimated_minutes": 60, "importance": 5, "flexibility": 1, "confidence_score": .9, "tasks": [], "missing_fields": []},
            {"title": "Prepare slides", "type": "hard_deadline", "estimated_minutes": None, "importance": 4, "flexibility": 2, "confidence_score": .6, "tasks": [], "missing_fields": ["estimated_minutes"]},
            {"title": "Team call", "type": "event", "estimated_minutes": None, "importance": 3, "flexibility": 1, "confidence_score": .9, "tasks": [], "missing_fields": ["duration"]},
            {"title": "Database assignment", "type": "hard_deadline", "estimated_minutes": None, "importance": 4, "flexibility": 1, "confidence_score": .8, "tasks": [], "missing_fields": ["estimated_minutes"]},
        ],
        "questions": [{"question": "How long should the first slide-preparation block be?", "context": "The effort estimate is uncertain."}],
    })
    gateway, traces = FakeModelGateway(structured=structured), MemoryTraces()
    app.dependency_overrides[get_model_gateway] = lambda: gateway
    app.dependency_overrides[get_repositories] = lambda: repositories(traces=traces)
    response = client.post("/api/v1/ai/intake", json={"text": text})
    assert response.status_code == 200
    assert [draft["title"] for draft in response.json()["drafts"]] == ["Authentication regression fix", "Prepare slides", "Team call", "Database assignment"]
    assert response.json()["drafts"][1]["missing_fields"] == ["estimated_minutes"]
    assert response.json()["questions"][0]["context"] == "The effort estimate is uncertain."
