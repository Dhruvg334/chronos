from typing import Dict, Any, List
from datetime import datetime, timezone
import logging

from postgrest.exceptions import APIError

from app.core.database import supabase_client

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


def get_time_spine_view(commitment_id: str, user_id: str) -> Dict[str, Any]:
    """
    Fetch and normalize a commitment time spine.

    This helper is intentionally defensive. Some Phase 3 endpoints should still
    complete if a spine is missing, malformed, or if mocked tests provide a
    non-UUID placeholder commitment id. In those cases, return an empty spine
    view instead of crashing the focus/reflection lifecycle.
    """
    if not supabase_client:
        return _empty_time_spine_view()

    try:
        spine_res = (
            supabase_client.table("time_spines")
            .select("*")
            .eq("commitment_id", commitment_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
    except APIError as exc:
        logger.warning("Unable to fetch time spine for commitment %s: %s", commitment_id, exc)
        return _empty_time_spine_view()

    if not spine_res.data:
        return _empty_time_spine_view()

    try:
        comm_res = (
            supabase_client.table("commitments")
            .select("risk_level")
            .eq("id", commitment_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        risk_level = comm_res.data.get("risk_level") if comm_res.data else "stable"
    except APIError as exc:
        logger.warning("Unable to fetch risk level for commitment %s: %s", commitment_id, exc)
        risk_level = "stable"

    spine_json = spine_res.data.get("spine_json") or []
    current_stage = spine_res.data.get("current_stage")

    return {
        "stages": normalize_spine_json(spine_json, current_stage, risk_level),
        "current_stage": current_stage,
    }


def advance_time_spine_stage(commitment_id: str, user_id: str, event_type: str = "progress") -> None:
    """Advance the current stage when possible; never break the parent operation."""
    if not supabase_client:
        return

    try:
        spine_res = (
            supabase_client.table("time_spines")
            .select("*")
            .eq("commitment_id", commitment_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
    except APIError as exc:
        logger.warning("Unable to advance time spine for commitment %s: %s", commitment_id, exc)
        return

    if not spine_res.data:
        return

    spine = spine_res.data
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
            (
                supabase_client.table("time_spines")
                .update({"current_stage": next_stage, "spine_json": spine_json})
                .eq("id", spine["id"])
                .eq("user_id", user_id)
                .execute()
            )
            logger.info("Advanced time spine for commitment %s to stage %s", commitment_id, next_stage)
        except APIError as exc:
            logger.warning("Failed to persist time spine advance for commitment %s: %s", commitment_id, exc)
