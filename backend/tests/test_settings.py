from fastapi.testclient import TestClient

from app.api.dependencies import get_repositories
from app.main import app
from tests.fakes import MemoryPlanningProfiles, repositories

client = TestClient(app)


def test_planning_profile_persists_and_resets():
    profiles = MemoryPlanningProfiles()
    app.dependency_overrides[get_repositories] = lambda: repositories(profiles=profiles)
    payload = {**profiles.DEFAULTS, "timezone": "Asia/Kolkata", "available_weekdays": [0, 1, 2, 3, 4, 5], "working_start_time": "09:30", "working_end_time": "18:30", "daily_focus_limit_minutes": 300, "protected_interval_start": "13:00", "protected_interval_end": "14:00"}
    saved = client.put("/api/v1/settings/planning-profile", json=payload)
    assert saved.status_code == 200
    assert saved.json()["timezone"] == "Asia/Kolkata"
    assert saved.json()["available_weekdays"] == [0, 1, 2, 3, 4, 5]
    reset = client.post("/api/v1/settings/planning-profile/reset")
    assert reset.status_code == 200
    assert reset.json()["timezone"] == "UTC"


def test_planning_profile_rejects_invalid_timezone_and_intervals():
    app.dependency_overrides[get_repositories] = lambda: repositories()
    invalid = {**MemoryPlanningProfiles.DEFAULTS, "timezone": "Not/A_Zone"}
    assert client.put("/api/v1/settings/planning-profile", json=invalid).status_code == 422
    invalid = {**MemoryPlanningProfiles.DEFAULTS, "protected_interval_start": "14:00", "protected_interval_end": "13:00"}
    assert client.put("/api/v1/settings/planning-profile", json=invalid).status_code == 422
