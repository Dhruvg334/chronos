from fastapi.testclient import TestClient

from app.api.dependencies import get_repositories
from app.main import app
from tests.fakes import MemoryCommitments, MemoryPlanningProfiles, repositories

client = TestClient(app)
USER = "00000000-0000-0000-0000-000000000001"


def preference_payload(**updates):
    return {"planning_style": "guided", "recommendation_frequency": "normal", "approval_strictness": "always_ask", "internal_write_automation_enabled": False, "preferred_focus_durations": [25, 45], "routine_continuity_preference": "gentle", "quick_task_mode": "batch", "strategy_preferences": ["task_batching", "quick_action", "eisenhower_triage", "time_blocking"], "explanation_detail": "detailed", **updates}


def item():
    return {"id": "c1", "user_id": USER, "title": "Release fix", "description": "Run tests", "status": "active", "type": "hard_deadline", "estimated_minutes": 60, "actual_minutes": 0, "importance": 5, "risk_level": "critical", "risk_score": 85, "confidence_score": .9}


def test_preferences_persist_and_change_strategy_explanation_and_focus_options():
    profiles = MemoryPlanningProfiles({USER: preference_payload()})
    commitments = MemoryCommitments([item()], tasks=[{"id": "t1", "user_id": USER, "status": "active", "estimated_minutes": 5}, {"id": "t2", "user_id": USER, "status": "active", "estimated_minutes": 5}])
    repos = repositories(profiles=profiles, commitments=commitments)
    app.dependency_overrides[get_repositories] = lambda: repos
    assert client.put("/api/v1/settings/preferences", json=preference_payload()).status_code == 200
    today = client.get("/api/v1/today").json()
    assert today["strategy_recommendation"]["strategy"] == "task_batching"
    assert today["explanation"]["detail"] == "detailed"
    assert today["focus_duration_options"] == [25, 45]


def test_minimal_low_frequency_hides_low_value_guidance_and_unsafe_automation():
    profiles = MemoryPlanningProfiles({USER: preference_payload(planning_style="minimal", recommendation_frequency="low", explanation_detail="brief", quick_task_mode="immediate")})
    commitment = item(); commitment.update(risk_level="watch", risk_score=30, importance=2)
    app.dependency_overrides[get_repositories] = lambda: repositories(profiles=profiles, commitments=MemoryCommitments([commitment]))
    today = client.get("/api/v1/today").json()
    assert today["strategy_recommendation"] is None
    assert today["explanation"]["constraints_considered"] == []
    unsafe = preference_payload(approval_strictness="always_ask", internal_write_automation_enabled=True)
    assert client.put("/api/v1/settings/preferences", json=unsafe).status_code == 422


def test_feedback_is_concise_owned_and_dismisses_matching_strategy():
    profiles = MemoryPlanningProfiles({USER: preference_payload()})
    repos = repositories(profiles=profiles, commitments=MemoryCommitments([item()]))
    app.dependency_overrides[get_repositories] = lambda: repos
    response = client.post("/api/v1/recommendations/feedback", json={"recommendation_type": "strategy", "recommendation_key": "eisenhower_triage", "context_summary": {"surface": "today", "raw_prompt": "must not persist"}, "user_action": "dismissed"})
    assert response.status_code == 201
    stored = repos.feedback.list_for_user(USER)[0]
    assert stored["context_summary"] == {"surface": "today"}
    assert client.get("/api/v1/today").json()["strategy_recommendation"] is None
