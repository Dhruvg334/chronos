from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_repositories
from app.core.config import settings
from app.repositories.protocols import RepositorySet
from app.schemas.planning_profile import IntegrationStatus, PlanningProfile, PlanningProfileResponse

router = APIRouter()


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


@router.get("/integrations", response_model=list[IntegrationStatus])
def get_integration_status(
    user_id: str = Depends(get_current_user),
    repositories: RepositorySet = Depends(get_repositories),
):
    configured = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    raw = repositories.google_connections.get_status(user_id)
    state = raw.get("state", "unavailable") if configured else "configuration_missing"
    messages = {
        "connected": "Calendar events are included in planning. ChronOS has read-only access.",
        "disconnected": "Connect Google Calendar to include busy time in plans.",
        "unavailable": "Calendar status is temporarily unavailable. Planning is using your availability profile only.",
        "configuration_missing": "Calendar connection is not configured. Planning is using your availability profile only.",
    }
    return [IntegrationStatus(
        state=state,
        last_successful_sync=raw.get("last_successful_sync"),
        retry_available=state in {"connected", "unavailable"},
        planning_mode="calendar_and_profile" if state == "connected" else "profile_only",
        message=messages[state],
    )]
