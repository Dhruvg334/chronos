from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_repositories
from app.repositories.protocols import RepositorySet
from app.schemas.personalization import RecommendationFeedbackCreate

router = APIRouter()

SAFE_CONTEXT_KEYS = {"surface", "failure_mode", "confidence", "planning_style", "strategy", "commitment_id", "option_id"}


def concise_context(value: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in SAFE_CONTEXT_KEYS:
        if key not in value:
            continue
        item = value.get(key)
        if isinstance(item, (str, int, float, bool)) or item is None:
            result[key] = str(item)[:160] if isinstance(item, str) else item
    return result


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def create_feedback(request: RecommendationFeedbackCreate, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    row = repositories.feedback.create(user_id, {
        "id": str(uuid.uuid4()),
        "recommendation_type": request.recommendation_type,
        "recommendation_key": request.recommendation_key,
        "context_summary": concise_context(request.context_summary),
        "user_action": request.user_action,
        "reason_category": request.reason_category,
    })
    return {"id": row["id"], "status": "recorded"}
