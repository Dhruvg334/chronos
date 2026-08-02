from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import get_model_gateway, get_repositories
from app.main import app
from app.models.fake import FakeModelGateway
from app.repositories.protocols import RepositorySet
from app.schemas.intake import IntakeResponse


class FakeCommitmentsRepository:
    def __init__(self):
        self.created = []
        self.tasks = []

    def list_for_user(self, user_id): return []
    def get_for_user(self, user_id, commitment_id): return None
    def create(self, user_id, data):
        self.created.append({**data, "user_id": user_id})
        return self.created[-1]
    def create_tasks(self, user_id, rows): self.tasks.extend(rows)
    def create_time_spine(self, user_id, data): return None


class NoopRepository:
    def list_for_user(self, user_id): return []
    def list_pending(self, user_id): return []
    def list_recent(self, user_id, commitment_id): return []
    def append(self, user_id, run_id, event): return None
    def get_metadata(self, user_id): return None


def repository_set(commitments=None):
    noop = NoopRepository()
    return RepositorySet(commitments or FakeCommitmentsRepository(), noop, noop, noop, noop, noop)


client = TestClient(app)


def test_intake_process_success():
    run_id = str(uuid4())
    gateway = FakeModelGateway(structured=IntakeResponse(agent_run_id=run_id, drafts=[], questions=[]))
    app.dependency_overrides[get_model_gateway] = lambda: gateway
    with patch("app.api.v1.intake.create_agent_run", return_value=run_id), patch("app.api.v1.intake.update_agent_run"):
        response = client.post("/api/v1/ai/intake", json={"text": "Finish the report tomorrow"})
    assert response.status_code == 200
    assert response.json()["agent_run_id"] == run_id
    assert gateway.calls


def test_approve_empty():
    app.dependency_overrides[get_repositories] = lambda: repository_set()
    response = client.post("/api/v1/ai/intake/approve", json={"agent_run_id": str(uuid4()), "approved_drafts": []})
    assert response.status_code == 400


def test_approve_success():
    commitments = FakeCommitmentsRepository()
    app.dependency_overrides[get_repositories] = lambda: repository_set(commitments)
    draft = {"title": "Do a thing", "type": "task", "estimated_minutes": 30, "importance": 3, "flexibility": 3, "confidence_score": 0.9, "tasks": [], "missing_fields": []}
    with patch("app.api.v1.intake.AgentTraceLogger"):
        response = client.post("/api/v1/ai/intake/approve", json={"agent_run_id": str(uuid4()), "approved_drafts": [draft]})
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert len(commitments.created) == 1
