from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_repositories
from app.repositories.protocols import RepositorySet
from app.schemas.core import StrategyRecommendationRequest, StrategyRecommendationResponse, TodayResponse
from app.services.core_journey import CoreJourneyService
from app.strategies.selector import StrategySelector
from app.strategies.models import StrategyId, StrategyPreferences
from app.schemas.planning_profile import PlanningProfile

router = APIRouter()


@router.get("", response_model=TodayResponse)
async def get_today(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return CoreJourneyService(repositories).today(user_id)


@router.post("/strategy", response_model=StrategyRecommendationResponse)
async def get_strategy_recommendation(request: StrategyRecommendationRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    if request.context is not None:
        profile = PlanningProfile.model_validate(repositories.planning_profiles.get(user_id))
        enabled = {StrategyId(value) for value in profile.strategy_preferences if value in {item.value for item in StrategyId}}
        preferences = StrategyPreferences(enabled=enabled, quick_task_threshold_minutes=min(profile.quick_task_threshold_minutes, 15), focus_minutes=profile.default_focus_duration_minutes, quick_task_mode=profile.quick_task_mode)
        return StrategyRecommendationResponse(recommendation=StrategySelector().recommend(request.context, preferences))
    return StrategyRecommendationResponse(recommendation=CoreJourneyService(repositories).today(user_id).strategy_recommendation)
