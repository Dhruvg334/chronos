from fastapi.testclient import TestClient

from app.api.dependencies import get_repositories
from app.main import app
from tests.fakes import MemoryPlanningProfiles, repositories

client = TestClient(app)


def payload(profiles: MemoryPlanningProfiles, **updates):
    return {**profiles.DEFAULTS, "timezone": "Asia/Kolkata", "available_weekdays": [0, 1, 2, 3, 4, 5], "working_start_time": "09:30", "working_end_time": "18:30", "protected_interval_start": "13:00", "protected_interval_end": "14:00", "daily_focus_limit_minutes": 300, "default_focus_duration_minutes": 45, "minimum_transition_buffer_minutes": 10, "quick_task_threshold_minutes": 5, "planning_style": "balanced", **updates}


def test_onboarding_saves_resumes_completes_and_does_not_reappear():
    profiles = MemoryPlanningProfiles()
    app.dependency_overrides[get_repositories] = lambda: repositories(profiles=profiles)
    saved = client.put("/api/v1/settings/onboarding", json=payload(profiles, onboarding_step=2, complete=False))
    assert saved.status_code == 200
    assert saved.json()["onboarding_status"] == "in_progress" and saved.json()["onboarding_step"] == 2
    resumed = client.get("/api/v1/settings/onboarding").json()
    assert resumed["timezone"] == "Asia/Kolkata"
    completed = client.put("/api/v1/settings/onboarding", json={**resumed, "complete": True})
    assert completed.json()["onboarding_status"] == "completed"
    assert client.get("/api/v1/settings/onboarding").json()["onboarding_status"] == "completed"


def test_onboarding_skip_and_reopen_are_explicit():
    profiles = MemoryPlanningProfiles()
    app.dependency_overrides[get_repositories] = lambda: repositories(profiles=profiles)
    assert client.post("/api/v1/settings/onboarding/skip").json()["onboarding_status"] == "skipped"
    reopened = client.post("/api/v1/settings/onboarding/reopen").json()
    assert reopened["onboarding_status"] == "in_progress" and reopened["onboarding_step"] == 1
