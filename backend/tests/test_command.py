import pytest
from unittest.mock import patch, MagicMock
from app.api.v1.command import run_command_analysis, load_judge_demo
from datetime import datetime, timezone, timedelta

@patch("app.api.v1.command.supabase_client")
@patch("app.api.v1.command.find_rescue_candidates")
@patch("app.api.v1.command.get_layered_capacity")
def test_run_command_analysis_rescue_required(mock_capacity, mock_rescue, mock_supabase):
    mock_capacity.return_value = {"available_minutes": 100, "capacity_source": "mock"}
    mock_rescue.return_value = [{"id": "1"}]
    
    now = datetime.now(timezone.utc)
    mock_supabase.table().select().eq().execute.return_value.data = [
        {
            "id": "1",
            "status": "active",
            "deadline_at": (now - timedelta(hours=1)).isoformat(),
            "risk_level": "rescue_required",
            "estimated_minutes": 60,
            "actual_minutes": 0
        }
    ]
    mock_supabase.table().select().eq().eq().execute.return_value.data = []
    
    result = run_command_analysis("user123")
    assert result["time_health"] == "Rescue Required"
    assert "intervention" in result["time_health_explanation"]
    assert result["rescue_candidate_count"] == 1

@patch("app.api.v1.command.supabase_client")
@patch("app.api.v1.command.find_rescue_candidates")
@patch("app.api.v1.command.get_layered_capacity")
def test_run_command_analysis_stable(mock_capacity, mock_rescue, mock_supabase):
    mock_capacity.return_value = {"available_minutes": 500, "capacity_source": "mock"}
    mock_rescue.return_value = []
    
    now = datetime.now(timezone.utc)
    mock_supabase.table().select().eq().execute.return_value.data = [
        {
            "id": "1",
            "status": "active",
            "deadline_at": (now + timedelta(days=5)).isoformat(),
            "risk_level": "stable",
            "estimated_minutes": 60,
            "actual_minutes": 0
        }
    ]
    mock_supabase.table().select().eq().eq().execute.return_value.data = []
    
    result = run_command_analysis("user123")
    assert result["time_health"] == "Stable"

@patch("app.api.v1.command.supabase_client")
def test_load_judge_demo(mock_supabase):
    result = load_judge_demo("user123")
    assert result["status"] == "Demo scenario loaded successfully."
    mock_supabase.table.assert_any_call("commitments")
