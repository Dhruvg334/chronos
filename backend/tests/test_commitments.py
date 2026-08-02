from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user, get_repositories
from app.main import app
from tests.fakes import MemoryCommitments, repositories

client = TestClient(app)


def test_get_commitment_detail_uses_repositories():
    user_id = str(uuid4())
    commitment_id = str(uuid4())
    commitment = {
        "id": commitment_id, "user_id": user_id, "title": "Research proposal",
        "type": "hard_deadline", "status": "active", "estimated_minutes": 120,
        "actual_minutes": 0, "importance": 3, "flexibility": 3,
        "progress_percent": 0, "risk_score": 20.0, "risk_level": "stable",
        "confidence_score": 1.0,
    }
    app.dependency_overrides[get_current_user] = lambda: user_id
    app.dependency_overrides[get_repositories] = lambda: repositories(commitments=MemoryCommitments([commitment]))
    response = client.get(f"/api/v1/commitments/{commitment_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Research proposal"
    assert data["tasks"] == []
    assert data["time_spine_stages"] == []
    assert data["focus_blocks"] == []
    assert data["reflections"] == []
