import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_supabase():
    with patch("app.api.v1.focus_blocks.supabase_client") as mock:
        yield mock

def test_create_focus_block(mock_supabase):
    mock_run_id = str(uuid4())
    mock_user_id = str(uuid4())
    
    # Mock commitment check
    mock_supabase.table().select().eq().eq().execute.return_value = MagicMock(data=[{"id": "123"}])
    
    # Mock insert
    mock_supabase.table().insert().execute.return_value = MagicMock(data=[{"id": mock_run_id, "status": "scheduled"}])
    
    req = {
        "commitment_id": "123",
        "title": "Deep Work",
        "start_at": datetime.now(timezone.utc).isoformat(),
        "end_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "block_type": "deep_work"
    }
    
    with patch("app.api.dependencies.get_current_user", return_value=mock_user_id):
        from app.api.dependencies import get_current_user
        app.dependency_overrides[get_current_user] = lambda: mock_user_id
        res = client.post("/api/v1/focus-blocks", json=req)
        assert res.status_code == 200
        assert res.json()["status"] == "scheduled"
        
def test_complete_focus_block(mock_supabase):
    mock_user_id = str(uuid4())
    mock_block_id = str(uuid4())
    
    start = datetime.now(timezone.utc)
    end = start + timedelta(hours=1)
    
    mock_supabase.table().select().eq().eq().single().execute.return_value = MagicMock(
        data={"id": mock_block_id, "commitment_id": "123", "start_at": start.isoformat(), "end_at": end.isoformat()}
    )
    
    mock_supabase.table().select().eq().single().execute.return_value = MagicMock(
        data={"id": "123", "estimated_minutes": 60, "actual_minutes": 0, "progress_percent": 0.0}
    )
    
    mock_supabase.table().insert().execute.return_value = MagicMock(data=[{"id": "refl_1"}])
    mock_supabase.table().update().eq().execute.return_value = MagicMock(data=[{"id": "123", "actual_minutes": 60}])
    
    req = {
        "actual_minutes": 60,
        "completion_status": "completed",
        "energy_level": 4,
        "quality_confidence": "high",
        "progress_percent_update": 100.0
    }
    
    with patch("app.api.v1.focus_blocks.advance_time_spine_stage"):
        with patch("app.api.dependencies.get_current_user", return_value=mock_user_id):
            from app.api.dependencies import get_current_user
            app.dependency_overrides[get_current_user] = lambda: mock_user_id
            res = client.post(f"/api/v1/focus-blocks/{mock_block_id}/complete", json=req)
            assert res.status_code == 200
        assert "reflection" in res.json()
        assert "commitment" in res.json()
