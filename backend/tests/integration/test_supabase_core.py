from __future__ import annotations

import os
import uuid
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from supabase import create_client

from app.api.dependencies import get_current_user, get_repositories
from app.main import app
from app.repositories.supabase import create_repository_set
from app.services.core_journey import CoreJourneyService

pytestmark = pytest.mark.integration

ALPHA = "chronos.alpha@example.com"
BETA = "chronos.beta@example.com"
PASSWORD = "ChronOS-local-test-2026!"


def _config():
    if os.getenv("RUN_SUPABASE_INTEGRATION") != "1":
        pytest.skip("Set RUN_SUPABASE_INTEGRATION=1 to run local Supabase integration tests.")
    values = (
        os.getenv("SUPABASE_TEST_URL"),
        os.getenv("SUPABASE_TEST_ANON_KEY"),
        os.getenv("SUPABASE_TEST_SERVICE_ROLE_KEY"),
    )
    if not all(values):
        pytest.skip("Local Supabase integration environment is incomplete.")
    return values


@pytest.fixture(scope="module")
def live():
    url, anon_key, service_key = _config()
    admin = create_client(url, service_key)
    created = []
    for email in (ALPHA, BETA):
        response = admin.auth.admin.create_user({"email": email, "password": PASSWORD, "email_confirm": True})
        created.append(str(response.user.id))
    clients = []
    for email in (ALPHA, BETA):
        client = create_client(url, anon_key)
        client.auth.sign_in_with_password({"email": email, "password": PASSWORD})
        clients.append(client)
    yield admin, clients[0], clients[1], created[0], created[1]
    app.dependency_overrides.clear()
    for user_id in created:
        admin.auth.admin.delete_user(user_id)


def _commitment(user_id: str, title="Authentication fix"):
    return {
        "id": str(uuid.uuid4()), "user_id": user_id, "title": title, "type": "hard_deadline",
        "status": "active", "estimated_minutes": 90, "actual_minutes": 0,
        "importance": 5, "flexibility": 1, "progress_percent": 0,
        "risk_level": "critical", "risk_score": 80, "confidence_score": .9,
    }


def test_live_core_journey_transactions_and_rollback(live):
    admin, alpha, _, alpha_id, _ = live
    repositories = create_repository_set(admin)
    repositories.planning_profiles.update(alpha_id, {
        "timezone": "Asia/Kolkata", "available_weekdays": [0, 1, 2, 3, 4, 5],
        "working_start_time": "09:30", "working_end_time": "18:30",
        "daily_focus_limit_minutes": 300, "default_focus_duration_minutes": 45,
        "minimum_transition_buffer_minutes": 10,
        "minimum_daily_unscheduled_buffer_minutes": 60,
        "protected_interval_start": "13:00", "protected_interval_end": "14:00",
        "quick_task_threshold_minutes": 5,
    })
    now = datetime.now(timezone.utc)
    run_id = repositories.traces.create_run(alpha_id, "intake", {}, workflow_id=str(uuid.uuid4()))
    app.dependency_overrides[get_current_user] = lambda: alpha_id
    app.dependency_overrides[get_repositories] = lambda: repositories
    api = TestClient(app)
    approval = api.post("/api/v1/ai/intake/approve", headers={"Idempotency-Key": f"live-intake-{run_id}"}, json={"agent_run_id": run_id, "approved_drafts": [{"title": "Authentication fix", "type": "hard_deadline", "estimated_minutes": 90, "importance": 5, "flexibility": 1, "confidence_score": .9, "tasks": [{"title": "Run regression suite", "estimated_minutes": 45}], "missing_fields": []}]})
    assert approval.status_code == 200 and approval.json()["count"] == 1
    commitment = next(row for row in repositories.commitments.list_for_user(alpha_id) if row["title"] == "Authentication fix")
    today = api.get("/api/v1/today")
    assert today.status_code == 200 and today.json()["next_action"]["commitment_id"] == commitment["id"]

    zone = ZoneInfo("Asia/Kolkata")
    planning_day = now.astimezone(zone).date() + timedelta(days=1)
    while planning_day.weekday() not in {0, 1, 2, 3, 4, 5}:
        planning_day += timedelta(days=1)
    at = lambda value: datetime.combine(planning_day, value, zone)
    admin.table("calendar_events").insert([
        {"user_id": alpha_id, "title": "Team meeting", "start_at": at(time(11)).isoformat(), "end_at": at(time(12)).isoformat(), "source": "local_test"},
        {"user_id": alpha_id, "title": "Database review", "start_at": at(time(14, 30)).isoformat(), "end_at": at(time(15, 15)).isoformat(), "source": "local_test"},
    ]).execute()
    plan_before = api.get("/api/v1/plan", params={"start_at": at(time.min).isoformat(), "end_at": (at(time.min) + timedelta(days=1)).isoformat()})
    assert plan_before.status_code == 200
    capacity = plan_before.json()["capacity"]
    assert capacity["busy_minutes"] == 105
    assert capacity["total_available_minutes"] == 295
    assert capacity["remaining_minutes"] == 295
    protected = api.post("/api/v1/plan/blocks", json={"commitment_id": commitment["id"], "start_at": at(time(13, 15)).isoformat(), "duration_minutes": 30})
    assert protected.status_code == 409 and "protected interval" in protected.text
    transition = api.post("/api/v1/plan/blocks", json={"commitment_id": commitment["id"], "start_at": at(time(12, 5)).isoformat(), "duration_minutes": 30})
    assert transition.status_code == 409 and "transition" in transition.text
    created = api.post("/api/v1/plan/blocks", json={"commitment_id": commitment["id"], "start_at": at(time(15, 25)).isoformat(), "duration_minutes": 60})
    assert created.status_code == 201
    block = created.json()["block"]
    assert api.post(f"/api/v1/focus-blocks/{block['id']}/start").json()["session"]["status"] == "active"
    assert api.post(f"/api/v1/focus-blocks/{block['id']}/pause").json()["session"]["status"] == "paused"
    assert api.post(f"/api/v1/focus-blocks/{block['id']}/resume").json()["session"]["status"] == "active"
    completed = api.post(f"/api/v1/focus-blocks/{block['id']}/complete", headers={"Idempotency-Key": f"live-focus-{block['id']}"}, json={"actual_minutes": 20, "completion_status": "partial", "energy_level": 3, "progress_percent": 40})
    assert completed.status_code == 200 and completed.json()["reflection"]["energy_level"] == 3
    assert repositories.commitments.get_for_user(alpha_id, commitment["id"])["progress_percent"] == 40
    recovery = api.post(f"/api/v1/rescue/{commitment['id']}/plan")
    assert recovery.status_code == 200
    proposal = recovery.json()["proposals"][0]
    approved = api.post(f"/api/v1/rescue/proposals/{proposal['id']}/approve", headers={"Idempotency-Key": f"live-recovery-{proposal['id']}"})
    assert approved.status_code == 200 and approved.json()["status"] == "approved"

    rollback_commitment = _commitment(alpha_id, "Rollback sentinel")
    run_id = repositories.traces.create_run(alpha_id, "intake", {}, workflow_id=str(uuid.uuid4()))
    invalid = {**rollback_commitment, "description": None, "deadline_at": None, "start_before_at": None, "tasks": [{"id": str(uuid.uuid4()), "title": None, "sequence_order": 0}], "time_spine": {"id": str(uuid.uuid4()), "stages": [], "current_stage": "next_action"}}
    with pytest.raises(Exception):
        repositories.commitments.approve_intake(alpha_id, run_id, f"rollback-{uuid.uuid4()}", [invalid])
    assert repositories.commitments.get_for_user(alpha_id, rollback_commitment["id"]) is None

    failed_block = repositories.focus.create(alpha_id, {"id": str(uuid.uuid4()), "commitment_id": commitment["id"], "title": "Rollback focus", "start_at": now.isoformat(), "end_at": (now + timedelta(minutes=25)).isoformat(), "status": "active", "block_type": "deep_work", "started_at": now.isoformat()})
    with pytest.raises(Exception):
        repositories.focus.complete_transaction(alpha_id, {"p_focus_block_id": failed_block["id"], "p_reflection_id": str(uuid.uuid4()), "p_idempotency_key": f"rollback-focus-{uuid.uuid4()}", "p_actual_minutes": 5, "p_completion_status": "partial", "p_energy_level": 9, "p_progress_percent": 45, "p_risk_score": 55.0, "p_risk_level": "at_risk", "p_blocker_reason": None, "p_notes": None})
    assert repositories.focus.get_for_user(alpha_id, failed_block["id"])["status"] == "active"

    rollback_run = repositories.traces.create_run(alpha_id, "recovery", {}, workflow_id=str(uuid.uuid4()))
    rollback_proposal = repositories.planning.create_proposal(alpha_id, {"id": str(uuid.uuid4()), "agent_run_id": rollback_run, "action_type": "commitment_rescue", "status": "pending", "payload_json": {"rescue_action_type": "create_rescue_focus_block", "commitment_id": commitment["id"], "title": "Conflicting recovery", "start_at": now.isoformat(), "end_at": (now + timedelta(minutes=25)).isoformat()}, "explanation": "Rollback sentinel"})
    with pytest.raises(Exception):
        repositories.planning.approve_recovery(alpha_id, rollback_proposal["id"], f"rollback-recovery-{uuid.uuid4()}", str(uuid.uuid4()))
    assert repositories.planning.get_proposal(alpha_id, rollback_proposal["id"])["status"] == "pending"

    alpha.auth.sign_out()
    with pytest.raises(Exception, match="permission denied"):
        alpha.table("commitments").select("*").execute()


def test_rls_prevents_cross_user_reads_writes_and_approval(live):
    admin, _, beta, alpha_id, beta_id = live
    repositories = create_repository_set(admin)
    commitment = repositories.commitments.create(alpha_id, _commitment(alpha_id, "Alpha only"))
    now = datetime.now(timezone.utc)
    focus = repositories.focus.create(alpha_id, {"id": str(uuid.uuid4()), "commitment_id": commitment["id"], "title": "Alpha focus", "start_at": now.isoformat(), "end_at": (now + timedelta(minutes=25)).isoformat(), "status": "scheduled", "block_type": "deep_work"})
    reflection = repositories.reflections.create(alpha_id, {"id": str(uuid.uuid4()), "commitment_id": commitment["id"], "focus_block_id": focus["id"], "planned_minutes": 25, "actual_minutes": 20, "completion_status": "partial", "energy_level": 3})
    run_id = repositories.traces.create_run(alpha_id, "recovery", {}, workflow_id=str(uuid.uuid4()))
    repositories.traces.append(alpha_id, run_id, {"step_name": "seed", "status": "succeeded", "explanation": "RLS seed", "payload_json": {}})
    trace_id = admin.table("agent_trace_events").select("id").eq("agent_run_id", run_id).single().execute().data["id"]
    proposal = repositories.planning.create_proposal(alpha_id, {"id": str(uuid.uuid4()), "agent_run_id": run_id, "action_type": "commitment_rescue", "status": "pending", "payload_json": {"rescue_action_type": "compress_scope", "commitment_id": commitment["id"]}, "explanation": "Alpha only"})

    for table, record_id in (("commitments", commitment["id"]), ("focus_blocks", focus["id"]), ("reflections", reflection["id"]), ("agent_trace_events", trace_id), ("agent_proposed_actions", proposal["id"])):
        assert beta.table(table).select("*").eq("id", record_id).execute().data == []
        assert beta.table(table).update({"updated_at": now.isoformat()} if table not in {"reflections", "agent_trace_events"} else {"user_id": beta_id}).eq("id", record_id).execute().data == []
        assert beta.table(table).delete().eq("id", record_id).execute().data == []
        assert admin.table(table).select("id").eq("id", record_id).execute().data
    with pytest.raises(Exception):
        beta.rpc("approve_recovery_transaction", {"p_user_id": beta_id, "p_proposal_id": proposal["id"], "p_idempotency_key": f"rls-{uuid.uuid4()}", "p_focus_block_id": None}).execute()

    app.dependency_overrides[get_current_user] = lambda: beta_id
    app.dependency_overrides[get_repositories] = lambda: create_repository_set(beta)
    response = TestClient(app).get("/api/v1/today")
    assert response.status_code == 200
    assert response.json()["next_action"] is None
