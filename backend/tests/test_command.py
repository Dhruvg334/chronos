from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.api.v1.command import load_judge_demo, run_command_analysis


class _ExecResult:
    def __init__(self, data):
        self.data = data


class _TableChain:
    def __init__(self, data=None):
        self.data = data or []

    def select(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        self.insert_payload = args[0] if args else None
        return self

    def delete(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def like(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def execute(self):
        return _ExecResult(self.data)


@patch("app.api.v1.command.run_scheduling_graph")
@patch("app.api.v1.command.supabase_client")
@patch("app.api.v1.command.find_rescue_candidates")
@patch("app.api.v1.command.get_layered_capacity")
def test_run_command_analysis_rescue_required(mock_capacity, mock_rescue, mock_supabase, mock_schedule):
    mock_capacity.return_value = {"available_minutes": 100, "capacity_source": "mock"}
    mock_rescue.return_value = [{"id": "1"}]
    mock_schedule.return_value = {"agent_run_id": "run1", "proposals": [{"id": "p1"}]}

    now = datetime.now(timezone.utc)
    commitments = [
        {
            "id": "1",
            "status": "active",
            "title": "Overdue task",
            "deadline_at": (now - timedelta(hours=1)).isoformat(),
            "risk_level": "rescue_required",
            "estimated_minutes": 60,
            "actual_minutes": 0,
        }
    ]
    proposals = [{"id": "p1", "action_type": "create_focus_block"}]

    def table_side_effect(name):
        if name == "commitments":
            return _TableChain(commitments)
        if name == "agent_proposed_actions":
            return _TableChain(proposals)
        return _TableChain([])

    mock_supabase.table.side_effect = table_side_effect

    result = run_command_analysis("user123")

    assert result["time_health"] == "Rescue Required"
    assert "intervention" in result["time_health_explanation"]
    assert result["rescue_candidate_count"] == 1
    assert result["schedule_proposal_count"] == 1
    assert result["pending_approval_count"] == 1
    assert result["scheduling_result"]["success"] is True
    mock_capacity.assert_called_once()
    mock_schedule.assert_called_once_with("user123")


@patch("app.api.v1.command.run_scheduling_graph")
@patch("app.api.v1.command.supabase_client")
@patch("app.api.v1.command.find_rescue_candidates")
@patch("app.api.v1.command.get_layered_capacity")
def test_run_command_analysis_stable(mock_capacity, mock_rescue, mock_supabase, mock_schedule):
    mock_capacity.return_value = {"available_minutes": 500, "capacity_source": "mock"}
    mock_rescue.return_value = []
    mock_schedule.return_value = {"agent_run_id": "run1", "proposals": []}

    now = datetime.now(timezone.utc)
    commitments = [
        {
            "id": "1",
            "status": "active",
            "title": "Future task",
            "deadline_at": (now + timedelta(days=5)).isoformat(),
            "risk_level": "stable",
            "estimated_minutes": 60,
            "actual_minutes": 0,
        }
    ]

    def table_side_effect(name):
        if name == "commitments":
            return _TableChain(commitments)
        if name == "agent_proposed_actions":
            return _TableChain([])
        return _TableChain([])

    mock_supabase.table.side_effect = table_side_effect

    result = run_command_analysis("user123")
    assert result["time_health"] == "Stable"
    assert result["warnings"] == []


@patch("app.api.v1.command.run_scheduling_graph")
@patch("app.api.v1.command.supabase_client")
@patch("app.api.v1.command.find_rescue_candidates")
@patch("app.api.v1.command.get_layered_capacity")
def test_run_command_analysis_does_not_fail_when_scheduler_fails(mock_capacity, mock_rescue, mock_supabase, mock_schedule):
    mock_capacity.return_value = {"available_minutes": 240, "capacity_source": "mock"}
    mock_rescue.return_value = []
    mock_schedule.side_effect = RuntimeError("graph failed")
    mock_supabase.table.return_value = _TableChain([
        {
            "id": "1",
            "status": "active",
            "title": "Task",
            "deadline_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "risk_level": "stable",
            "estimated_minutes": 60,
            "actual_minutes": 0,
        }
    ])

    result = run_command_analysis("user123")
    assert result["scheduling_result"]["success"] is False
    assert result["warnings"]


@patch("app.api.v1.command.supabase_client")
def test_load_judge_demo_is_user_scoped_and_cleans_demo_records(mock_supabase):
    mock_table = _TableChain([])
    mock_supabase.table.return_value = mock_table

    result = load_judge_demo("user123")

    assert result["status"] == "Demo scenario loaded successfully."
    assert result["commitments_loaded"] == 3
    mock_supabase.table.assert_any_call("focus_blocks")
    mock_supabase.table.assert_any_call("agent_proposed_actions")
    mock_supabase.table.assert_any_call("commitments")
