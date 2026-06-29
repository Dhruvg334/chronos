import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_supabase():
    with patch("app.api.v1.commitments.supabase_client") as mock:
        yield mock

def test_get_commitment_detail(mock_supabase):
    mock_user_id = str(uuid4())
    mock_comm_id = str(uuid4())
    
    mock_comm = {
        "id": mock_comm_id,
        "title": "Hackathon",
        "type": "project",
        "status": "active",
        "estimated_minutes": 120,
        "actual_minutes": 0,
        "importance": 3,
        "flexibility": 3,
        "progress_percent": 0.0,
        "risk_score": 20.0,
        "risk_level": "stable",
        "confidence_score": 1.0
    }
    
    # Mock sequence of db calls
    # 1. Commitment
    mock_supabase.table().select().eq().eq().single().execute.return_value = MagicMock(data=mock_comm)
    # 2. Tasks
    mock_supabase.table().select().eq().order().execute.return_value = MagicMock(data=[])
    # 3. Focus blocks
    mock_supabase.table().select().eq().order().execute.return_value = MagicMock(data=[])
    # 4. Reflections
    mock_supabase.table().select().eq().order().limit().execute.return_value = MagicMock(data=[])
    # Time spine is queried inside time_spine_service, so we mock that too
    with patch("app.api.v1.commitments.get_time_spine_view", return_value={"stages": [], "current_stage": None}):
        with patch("app.api.dependencies.get_current_user", return_value=mock_user_id):
            from app.api.dependencies import get_current_user
            app.dependency_overrides[get_current_user] = lambda: mock_user_id
            res = client.get(f"/api/v1/commitments/{mock_comm_id}")
            assert res.status_code == 200
            data = res.json()
            assert data["title"] == "Hackathon"
            assert "tasks" in data
            assert "time_spine_stages" in data
            assert "focus_blocks" in data
            assert "reflections" in data
