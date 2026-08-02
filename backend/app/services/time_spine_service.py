from typing import Dict, Any, List
from datetime import datetime, timezone
import logging

from app.repositories.protocols import CommitmentsRepository

logger = logging.getLogger(__name__)


def normalize_spine_json(spine_json: List[Dict[str, Any]], current_stage: str, risk_level: str) -> List[Dict[str, Any]]:
    """Normalize raw spine JSON into a frontend-friendly shape."""
    normalized = []
    found_current = False

    for i, stage in enumerate(spine_json or []):
        stage_id = stage.get("id") or stage.get("key") or f"stage_{i}"

        status = stage.get("status", "pending")
        if status == "pending" and not found_current:
            if stage_id == current_stage:
                status = "active"
                found_current = True
            else:
                status = "completed"
        elif status == "pending" and found_current:
            status = "pending"
        elif stage_id == current_stage:
            status = "active"
            found_current = True

        normalized.append({
            "key": stage_id,
            "label": stage.get("label", stage_id),
            "order": i,
            "status": status,
            "timestamp": stage.get("timestamp"),
            "risk_level": risk_level if status == "active" else None,
            "explanation": stage.get("explanation"),
        })
    return normalized


def _empty_time_spine_view() -> Dict[str, Any]:
    return {"stages": [], "current_stage": None}


def get_time_spine_view(commitment_id: str, user_id: str, repository: CommitmentsRepository) -> Dict[str, Any]:
    """
    Fetch and normalize a commitment time spine.

    This helper is intentionally defensive. Some Phase 3 endpoints should still
    complete if a spine is missing, malformed, or if mocked tests provide a
    non-UUID placeholder commitment id. In those cases, return an empty spine
    view instead of crashing the focus/reflection lifecycle.
    """
    try:
        spine = repository.get_time_spine(user_id, commitment_id)
    except Exception as exc:
        logger.warning("Unable to fetch time spine for commitment %s: %s", commitment_id, exc)
        return _empty_time_spine_view()
    if not spine:
        return _empty_time_spine_view()
    try:
        commitment = repository.get_for_user(user_id, commitment_id)
        risk_level = commitment.get("risk_level", "stable") if commitment else "stable"
    except Exception as exc:
        logger.warning("Unable to fetch risk level for commitment %s: %s", commitment_id, exc)
        risk_level = "stable"
    spine_json = spine.get("spine_json") or []
    current_stage = spine.get("current_stage")

    return {
        "stages": normalize_spine_json(spine_json, current_stage, risk_level),
        "current_stage": current_stage,
    }


def advance_time_spine_stage(commitment_id: str, user_id: str, repository: CommitmentsRepository, event_type: str = "progress") -> None:
    """Advance the current stage when possible; never break the parent operation."""
    try:
        spine = repository.get_time_spine(user_id, commitment_id)
    except Exception as exc:
        logger.warning("Unable to advance time spine for commitment %s: %s", commitment_id, exc)
        return
    if not spine:
        return
    spine_json = spine.get("spine_json") or []
    current_stage = spine.get("current_stage")

    next_stage = current_stage
    found = False

    for i, stage in enumerate(spine_json):
        if stage.get("id") == current_stage or stage.get("key") == current_stage:
            found = True
            if i + 1 < len(spine_json):
                next_stage = spine_json[i + 1].get("id") or spine_json[i + 1].get("key")
                stage["status"] = "completed"
                stage["timestamp"] = datetime.now(timezone.utc).isoformat()
            break

    if found and next_stage != current_stage:
        try:
            repository.update_time_spine(user_id, commitment_id, {"current_stage": next_stage, "spine_json": spine_json})
            logger.info("Advanced time spine for commitment %s to stage %s", commitment_id, next_stage)
        except Exception as exc:
            logger.warning("Failed to persist time spine advance for commitment %s: %s", commitment_id, exc)
