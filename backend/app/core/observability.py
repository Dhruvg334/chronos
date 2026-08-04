from __future__ import annotations

import contextvars
import json
import logging
import re
import time
import uuid
from contextlib import contextmanager
from typing import Any, Protocol

from fastapi import Request

request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
_SECRET_PATTERN = re.compile(r"(token|secret|api[_-]?key|authorization|password|cookie|raw.*(prompt|response|content|body)|email.*body|document.*text)", re.IGNORECASE)


class MetricsSink(Protocol):
    def increment(self, name: str, value: int = 1, **labels: str) -> None: ...
    def observe(self, name: str, value: float, **labels: str) -> None: ...


class NoOpMetrics:
    def increment(self, name: str, value: int = 1, **labels: str) -> None: pass
    def observe(self, name: str, value: float, **labels: str) -> None: pass


metrics: MetricsSink = NoOpMetrics()
_dependency_states: dict[str, tuple[str, float]] = {}


def configure_metrics(sink: MetricsSink) -> None:
    global metrics
    metrics = sink


def record_dependency_state(name: str, state: str) -> None:
    _dependency_states[name] = (state, time.monotonic())


def dependency_state(name: str, *, max_age_seconds: float = 300) -> str | None:
    value = _dependency_states.get(name)
    if not value or time.monotonic() - value[1] > max_age_seconds:
        return None
    return value[0]


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: "[REDACTED]" if _SECRET_PATTERN.search(str(key)) else redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str) and len(value) > 500:
        return value[:500] + "[TRUNCATED]"
    return value


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    payload = {"event": event, "request_id": request_id_context.get(), **redact(fields)}
    logger.log(level, json.dumps(payload, default=str, separators=(",", ":")))


@contextmanager
def observe_latency(metric_name: str, **labels: str):
    started = time.perf_counter()
    try:
        yield
    finally:
        metrics.observe(metric_name, (time.perf_counter() - started) * 1000, **labels)


async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_context.set(request_id)
    started = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration = round((time.perf_counter() - started) * 1000, 2)
        metrics.increment("http_requests_total", method=request.method)
        metrics.observe("http_request_duration_ms", duration, method=request.method)
        log_event(logging.getLogger("chronos.request"), logging.INFO, "request_completed",
                  method=request.method, path=request.url.path, duration_ms=duration)
        request_id_context.reset(token)
