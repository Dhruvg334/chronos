from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.core.errors import ChronosError
from app.schemas.planning_domains import RoutinePatch, WeeklyBlock
from app.services.planning_domains import PlanningDomainsService
from tests.fakes import MemoryFocus, repositories

USER = "00000000-0000-0000-0000-000000000001"
OTHER = "00000000-0000-0000-0000-000000000002"
WEEK = date(2026, 8, 3)


def profile():
    return {"timezone": "Asia/Kolkata", "available_weekdays": [0, 1, 2, 3, 4, 5], "working_start_time": "09:30:00", "working_end_time": "18:30:00", "daily_focus_limit_minutes": 300, "default_focus_duration_minutes": 45, "minimum_transition_buffer_minutes": 10, "minimum_daily_unscheduled_buffer_minutes": 60, "protected_interval_start": "13:00:00", "protected_interval_end": "14:00:00", "quick_task_threshold_minutes": 5}


def commitment(item_id="c1", **updates):
    return {"id": item_id, "user_id": USER, "title": "Authentication fix", "description": "Run regression tests", "status": "active", "type": "hard_deadline", "estimated_minutes": 90, "actual_minutes": 0, "importance": 5, "flexibility": 1, "risk_level": "critical", "risk_score": 80, "confidence_score": .9, **updates}


def service(**kwargs):
    repos = repositories(**kwargs)
    repos.planning_profiles.rows[USER] = profile()
    return PlanningDomainsService(repos), repos


def test_project_ownership_lifecycle_progress_and_archive():
    svc, repos = service()
    project = svc.create_project(USER, {"title": "ChronOS Production Release", "description": "Ship safely", "status": "active", "target_date": "2026-08-24", "colour": "accent"})
    assert svc.list_projects(OTHER) == []
    svc.create_outcome(USER, {"project_id": project["id"], "title": "Production deployment", "description": "", "status": "active", "target_date": "2026-08-20", "importance": 5, "estimated_effort_minutes": 120, "confidence": .8, "completion_criteria": "Service is healthy", "provenance": None})
    outcome = svc.create_outcome(USER, {"project_id": project["id"], "title": "Public documentation", "description": "", "status": "completed", "target_date": None, "importance": 4, "estimated_effort_minutes": 60, "confidence": .9, "completion_criteria": "Docs are public", "provenance": "inbox"})
    detail = svc.project_detail(USER, project["id"])
    assert detail["outcome_count"] == 2 and detail["progress_percent"] == 50 and outcome["provenance"] == "inbox"
    assert svc.update_project(USER, project["id"], {"status": "paused"})["status"] == "paused"
    assert svc.update_project(USER, project["id"], {"status": "archived"})["status"] == "archived"
    with pytest.raises(ChronosError): svc.project_detail(OTHER, project["id"])


def test_outcome_linking_completion_and_cross_user_rejection():
    svc, repos = service()
    project = svc.create_project(USER, {"title": "Release", "description": "", "status": "active", "target_date": None, "colour": "accent"})
    outcome = svc.create_outcome(USER, {"project_id": project["id"], "title": "Stable authentication", "description": "", "status": "active", "target_date": None, "importance": 5, "estimated_effort_minutes": 90, "confidence": .7, "completion_criteria": "Regression suite passes", "provenance": "inbox"})
    repos.commitments.rows.append(commitment())
    repos.commitments.tasks.append({"id": "t1", "user_id": USER, "commitment_id": "c1", "title": "Run suite"})
    svc.link_outcome_work(USER, outcome["id"], ["c1"], ["t1"])
    assert repos.commitments.rows[0]["outcome_id"] == outcome["id"] and repos.commitments.tasks[0]["outcome_id"] == outcome["id"]
    assert svc.update_outcome(USER, outcome["id"], {"status": "completed"})["status"] == "completed"
    with pytest.raises(ChronosError): svc.link_outcome_work(OTHER, outcome["id"], [], [])


def test_routine_schedule_minimum_version_pause_and_continuity_recovery():
    svc, _ = service()
    routine = svc.create_routine(USER, {"title": "Daily release review", "frequency_rule": "weekly", "preferred_days": [0,1,2,3,4,5], "preferred_time": "18:00:00", "minimum_viable_version": "5-minute blocker review", "estimated_duration_minutes": 20, "active": True})
    rows = svc.list_routines(USER, start=WEEK)
    assert len(rows[0]["occurrences"]) == 6 and all(item["date"] != "2026-08-09" for item in rows[0]["occurrences"])
    svc.record_routine(USER, routine["id"], {"occurrence_date": WEEK, "status": "skipped", "note": "release incident"})
    assert svc.list_routines(USER, start=WEEK)[0]["continuity_recovery"] == "5-minute blocker review"
    svc.record_routine(USER, routine["id"], {"occurrence_date": WEEK, "status": "minimum_completed", "note": None})
    assert svc.list_routines(USER, start=WEEK)[0]["continuity_recovery"] is None
    assert svc.update_routine(USER, routine["id"], {"active": False})["active"] is False
    with pytest.raises(ValueError):
        RoutinePatch(preferred_days=[0, 0])


def test_weekly_capacity_proposal_filters_blocked_work_and_approves_atomically():
    zone = ZoneInfo("Asia/Kolkata")
    svc, repos = service()
    project = svc.create_project(USER, {"title": "Release", "description": "", "status": "active", "target_date": "2026-08-24", "colour": "accent"})
    blocked = svc.create_outcome(USER, {"project_id": project["id"], "title": "Waiting deployment", "description": "", "status": "blocked", "target_date": "2026-08-10", "importance": 5, "estimated_effort_minutes": 90, "confidence": .8, "completion_criteria": "Host access arrives", "provenance": None})
    active = svc.create_outcome(USER, {"project_id": project["id"], "title": "Stable authentication", "description": "", "status": "active", "target_date": "2026-08-12", "importance": 5, "estimated_effort_minutes": 90, "confidence": .9, "completion_criteria": "Tests pass", "provenance": None})
    repos.commitments.rows.extend([commitment("blocked", outcome_id=blocked["id"], project_id=project["id"], status="blocked", title="Blocked deployment"), commitment("c1", outcome_id=active["id"], project_id=project["id"])])
    repos.planning.events.append({"id": "meeting", "user_id": USER, "title": "Team meeting", "start_at": datetime(2026,8,3,11,0,tzinfo=zone).isoformat(), "end_at": datetime(2026,8,3,12,0,tzinfo=zone).isoformat()})
    view = svc.weekly_view(USER, WEEK)
    assert len(view.days) == 7 and view.days[6].available_minutes == 0 and view.primary_strategy is not None
    proposal = svc.generate_weekly_proposal(USER, WEEK)
    assert all(block.commitment_id != "blocked" for block in proposal.blocks)
    assert all(not (block.start_at.hour == 13) for block in proposal.blocks)
    result = svc.approve_weekly_proposal(USER, proposal.id, "weekly-safe-key")
    assert result["status"] == "approved" and len(repos.focus.rows) == len(proposal.blocks)
    replay = repos.weekly_plans.approve(USER, proposal.id, "weekly-safe-key", result["block_ids"])
    assert replay["idempotent_replay"] is True


def test_weekly_edit_rejects_overlap_and_rejection_writes_no_blocks():
    zone = ZoneInfo("Asia/Kolkata")
    svc, repos = service()
    repos.commitments.rows.append(commitment())
    proposal = svc.generate_weekly_proposal(USER, WEEK)
    bad = [WeeklyBlock(commitment_id="c1", title="Authentication fix", start_at=datetime(2026,8,3,13,15,tzinfo=zone), duration_minutes=45)]
    with pytest.raises(ChronosError, match="protected"): svc.edit_weekly_proposal(USER, proposal.id, bad)
    rejected = svc.reject_weekly_proposal(USER, proposal.id)
    assert rejected.status == "rejected" and repos.focus.rows == []


def test_weekly_approval_failure_rolls_back_all_blocks():
    class FailingFocus(MemoryFocus):
        def create(self, user_id, data):
            if len(self.rows) == 1: raise RuntimeError("injected")
            return super().create(user_id, data)
    focus = FailingFocus()
    svc, repos = service(focus=focus)
    repos.commitments.rows.extend([commitment("c1"), commitment("c2", title="Documentation", estimated_minutes=60, risk_level="at_risk")])
    proposal = svc.generate_weekly_proposal(USER, WEEK)
    assert len(proposal.blocks) >= 2
    with pytest.raises(RuntimeError): svc.approve_weekly_proposal(USER, proposal.id, "weekly-rollback")
    assert repos.focus.rows == [] and repos.weekly_plans.get_for_user(USER, proposal.id)["status"] == "pending"
