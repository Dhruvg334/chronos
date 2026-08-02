from fastapi.testclient import TestClient

from app.api.dependencies import get_repositories
from app.main import app
from tests.fakes import MemoryCommitments, MemoryReflections, repositories

client = TestClient(app)
USER = "00000000-0000-0000-0000-000000000001"


def test_submit_contextual_reflection_through_repositories():
    commitments = MemoryCommitments([{"id": "c1", "user_id": USER, "title": "Fix", "status": "active", "estimated_minutes": 60, "actual_minutes": 0, "progress_percent": 0, "importance": 3, "flexibility": 3, "confidence_score": 1, "risk_score": 20, "risk_level": "stable"}])
    reflections = MemoryReflections()
    app.dependency_overrides[get_repositories] = lambda: repositories(commitments=commitments, reflections=reflections)
    response = client.post("/api/v1/reflection", json={"commitment_id": "c1", "planned_minutes": 30, "actual_minutes": 20, "completion_status": "partial", "energy_level": 3, "progress_percent": 40})
    assert response.status_code == 200
    assert response.json()["reflection"]["actual_minutes"] == 20
    assert commitments.rows[0]["progress_percent"] == 40
