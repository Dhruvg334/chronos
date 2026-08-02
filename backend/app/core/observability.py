from __future__ import annotations

import contextvars
import json
import logging
import re
import time
import uuid
from typing import Any

from fastapi import Request

request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
_SECRET_PATTERN = re.compile(r"(token|secret|api[_-]?key|authorization)", re.IGNORECASE)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: "[REDACTED]" if _SECRET_PATTERN.search(str(key)) else redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    payload = {"event": event, "request_id": request_id_context.get(), **redact(fields)}
    logger.log(level, json.dumps(payload, default=str, separators=(",", ":")))


async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_context.set(request_id)
    started = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        logging.getLogger("chronos.request").info(
            json.dumps({
                "event": "request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            })
        )
        request_id_context.reset(token)
