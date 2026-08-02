from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.core.config import settings
from app.core.container import container
from app.core.observability import log_event

logger = logging.getLogger("chronos.readiness")


def _database_check() -> None:
    client = container.database()
    client.table("user_profiles").select(
        "id,timezone,available_weekdays,working_start_time,working_end_time,daily_focus_limit_minutes"
    ).limit(1).execute()
    client.table("focus_blocks").select(
        "id,started_at,paused_at,accumulated_pause_seconds,stopped_reason"
    ).limit(1).execute()


async def readiness_report(*, check_model: bool = False) -> dict[str, Any]:
    database_configured = bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)
    database_state = "configuration_missing"
    if database_configured:
        try:
            await asyncio.wait_for(asyncio.to_thread(_database_check), timeout=1.5)
            database_state = "ready"
        except asyncio.TimeoutError:
            database_state = "timeout"
        except Exception as exc:
            name = type(exc).__name__
            database_state = "schema_incompatible" if "column" in str(exc).lower() else "unavailable"
            log_event(logger, logging.ERROR, "dependency_check_failed", dependency="database", classification=name)

    model_configured = bool(settings.LLM_PROVIDER == "groq" and settings.GROQ_API_KEY and settings.GROQ_MODEL_FAST)
    model_state = "configured" if model_configured else "configuration_missing"
    if check_model and model_configured:
        try:
            status = await asyncio.wait_for(container.model_gateway().health(), timeout=2.0)
            model_state = str(status.state)
        except Exception as exc:
            model_state = "unavailable"
            log_event(logger, logging.WARNING, "dependency_check_failed", dependency="model", classification=type(exc).__name__)

    google_configured = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    if database_state != "ready":
        status = "not_ready"
    elif model_state in {"unavailable", "configuration_missing", "degraded"} or not google_configured:
        status = "degraded"
    else:
        status = "ready"
    report = {
        "status": status,
        "environment": settings.ENV,
        "dependencies": {
            "database": {"required": True, "state": database_state, "timeout_ms": 1500},
            "model": {"required": False, "provider": settings.LLM_PROVIDER, "state": model_state, "checked": check_model},
            "google_calendar": {"required": False, "access": "read_only", "state": "configured" if google_configured else "configuration_missing"},
        },
    }
    log_event(logger, logging.INFO, "readiness_checked", status=status, dependencies={key: value["state"] for key, value in report["dependencies"].items()})
    return report
