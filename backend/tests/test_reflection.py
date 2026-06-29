import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_supabase():
    with patch("app.api.v1.reflection.supabase_client") as mock:
        yield mock

def test_submit_reflection(mock_supabase):
    mock_user_id = str(uuid4())
    mock_comm_id = str(uuid4())
    
    # 1. Mock commitment select
    mock_supabase.table().select().eq().eq().single().execute.return_value = MagicMock(
        data={"id": mock_comm_id, "estimated_minutes": 60, "actual_minutes": 0, "progress_percent": 0.0}
    )
    
    # 2. Mock reflection insert
    mock_supabase.table().insert().execute.return_value = MagicMock(data=[{"id": str(uuid4())}])
    
    # 3. Mock commitment update
    mock_supabase.table().update().eq().execute.return_value = MagicMock(data=[{"id": mock_comm_id, "actual_minutes": 30}])
    
    req = {
        "commitment_id": mock_comm_id,
        "planned_minutes": 30,
        "actual_minutes": 30,
        "completion_status": "completed",
        "energy_level": 5,
        "progress_percent_update": 50.0
    }
    
    with patch("app.api.v1.reflection.advance_time_spine_stage"):
        with patch("app.api.dependencies.get_current_user", return_value=mock_user_id):
            from app.api.dependencies import get_current_user
            app.dependency_overrides[get_current_user] = lambda: mock_user_id
            res = client.post("/api/v1/reflection", json=req)
            assert res.status_code == 200
        assert "reflection" in res.json()
        assert "commitment" in res.json()
