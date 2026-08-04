from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_repositories
from app.repositories.protocols import RepositorySet
from app.schemas.planning_profile import PlanningProfile, PlanningProfileResponse
from app.schemas.personalization import OnboardingSaveRequest, PreferenceUpdate

router = APIRouter()

PREFERENCE_FIELDS = (
    "planning_style", "recommendation_frequency", "approval_strictness",
    "internal_write_automation_enabled", "preferred_focus_durations",
    "routine_continuity_preference", "quick_task_mode", "strategy_preferences",
    "explanation_detail",
)


@router.get("/planning-profile", response_model=PlanningProfileResponse)
def get_planning_profile(
    user_id: str = Depends(get_current_user),
    repositories: RepositorySet = Depends(get_repositories),
):
    return repositories.planning_profiles.get(user_id)


@router.put("/planning-profile", response_model=PlanningProfileResponse)
def update_planning_profile(
    request: PlanningProfile,
    user_id: str = Depends(get_current_user),
    repositories: RepositorySet = Depends(get_repositories),
):
    return repositories.planning_profiles.update(user_id, request.model_dump(mode="json"))


@router.post("/planning-profile/reset", response_model=PlanningProfileResponse)
def reset_planning_profile(
    user_id: str = Depends(get_current_user),
    repositories: RepositorySet = Depends(get_repositories),
):
    return repositories.planning_profiles.reset(user_id)


@router.get("/onboarding", response_model=PlanningProfileResponse)
def get_onboarding(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return repositories.planning_profiles.get(user_id)


@router.put("/onboarding", response_model=PlanningProfileResponse)
def save_onboarding(request: OnboardingSaveRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    data = request.model_dump(mode="json", exclude={"complete", "onboarding_status", "onboarding_completed_at"})
    data["onboarding_status"] = "completed" if request.complete else "in_progress"
    if request.complete:
        data["onboarding_step"] = 3
        data["onboarding_completed_at"] = datetime.now(timezone.utc).isoformat()
    return repositories.planning_profiles.update(user_id, data)


@router.post("/onboarding/skip", response_model=PlanningProfileResponse)
def skip_onboarding(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return repositories.planning_profiles.update(user_id, {"onboarding_status": "skipped", "onboarding_completed_at": datetime.now(timezone.utc).isoformat()})


@router.post("/onboarding/reopen", response_model=PlanningProfileResponse)
def reopen_onboarding(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return repositories.planning_profiles.update(user_id, {"onboarding_status": "in_progress", "onboarding_step": 1, "onboarding_completed_at": None})


@router.get("/preferences")
def get_preferences(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    profile = repositories.planning_profiles.get(user_id)
    return {key: profile[key] for key in PREFERENCE_FIELDS}


@router.put("/preferences")
def update_preferences(request: PreferenceUpdate, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    current = repositories.planning_profiles.get(user_id)
    validated = PlanningProfile.model_validate({**current, **request.model_dump(mode="json")})
    updated = repositories.planning_profiles.update(user_id, {key: getattr(validated, key) for key in PREFERENCE_FIELDS})
    return {key: updated[key] for key in PREFERENCE_FIELDS}
