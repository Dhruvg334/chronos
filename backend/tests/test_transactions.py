from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from tests.fakes import MemoryCommitments, MemoryFocus, MemoryPlanning, MemoryReflections, repositories

USER = "00000000-0000-0000-0000-000000000001"


def test_intake_failure_rolls_back_commitment_tasks_and_spine():
    class FailingCommitments(MemoryCommitments):
        def create_tasks(self, user_id, rows):
            raise RuntimeError("injected task failure")

    store = FailingCommitments()
    repositories(commitments=store)
    item = {"id": str(uuid4()), "title": "Rollback", "tasks": [{"id": str(uuid4()), "title": "Fail"}], "time_spine": {"id": str(uuid4()), "stages": [], "current_stage": "next_action"}}
    with pytest.raises(RuntimeError):
        store.approve_intake(USER, str(uuid4()), f"intake-{uuid4()}", [item])
    assert store.rows == [] and store.tasks == [] and store.spines == []


def test_focus_failure_rolls_back_lifecycle_progress_reflection_and_spine():
    class FailingReflections(MemoryReflections):
        def create(self, user_id, data):
            raise RuntimeError("injected reflection failure")

    now = datetime.now(timezone.utc)
    commitments = MemoryCommitments([{"id": "c1", "user_id": USER, "actual_minutes": 0, "progress_percent": 0}])
    focus = MemoryFocus([{"id": "f1", "user_id": USER, "commitment_id": "c1", "start_at": now.isoformat(), "end_at": (now + timedelta(minutes=25)).isoformat(), "status": "active"}])
    repositories(commitments=commitments, focus=focus, reflections=FailingReflections())
    with pytest.raises(RuntimeError):
        focus.complete_transaction(USER, {"p_idempotency_key": f"focus-{uuid4()}", "p_focus_block_id": "f1", "p_reflection_id": str(uuid4()), "p_actual_minutes": 20, "p_completion_status": "partial", "p_energy_level": 3, "p_progress_percent": 40, "p_risk_score": 60, "p_risk_level": "at_risk"})
    assert focus.rows[0]["status"] == "active"
    assert commitments.rows[0]["progress_percent"] == 0


def test_recovery_failure_keeps_proposal_pending_and_creates_no_block():
    class FailingFocus(MemoryFocus):
        def create(self, user_id, data):
            raise RuntimeError("injected plan failure")

    proposal = {"id": "p1", "user_id": USER, "status": "pending", "payload_json": {"rescue_action_type": "create_rescue_focus_block", "commitment_id": "c1", "start_at": "2026-08-03T10:00:00+00:00", "end_at": "2026-08-03T10:25:00+00:00"}}
    planning, focus = MemoryPlanning(proposals=[proposal]), FailingFocus()
    repositories(planning=planning, focus=focus)
    with pytest.raises(RuntimeError):
        planning.approve_recovery(USER, "p1", f"recovery-{uuid4()}", str(uuid4()))
    assert planning.proposals[0]["status"] == "pending"
    assert focus.rows == []
