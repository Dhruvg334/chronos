from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from app.core.errors import ChronosError, ErrorCode


@dataclass
class WorkflowTraceEvent:
    workflow: str
    step: str
    reason_category: str
    outcome: str
    duration_ms: float
    tool_selected: str | None = None
    validation_result: str = "valid"
    provider: str | None = None
    model: str | None = None
    error_classification: str | None = None
    decision_summary: str = ""


@dataclass
class WorkflowContext:
    workflow_id: str
    user_id: str
    workflow: str
    max_steps: int
    timeout_seconds: float
    request_budget: int
    step_count: int = 0
    request_count: int = 0
    traces: list[WorkflowTraceEvent] = field(default_factory=list)


class WorkflowRunner:
    def __init__(self, *, max_steps: int, timeout_seconds: float, request_budget: int):
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds
        self.request_budget = request_budget

    def context(self, user_id: str, workflow: str) -> WorkflowContext:
        return WorkflowContext(str(uuid.uuid4()), user_id, workflow, self.max_steps, self.timeout_seconds, self.request_budget)

    async def run_step(self, context: WorkflowContext, name: str, reason_category: str, operation: Callable[[], Awaitable[Any]], *, provider: str | None = None, model: str | None = None) -> Any:
        if context.step_count >= context.max_steps:
            raise ChronosError(ErrorCode.WORKFLOW_FAILED, "This workflow reached its safe step limit.")
        context.step_count += 1
        started = time.perf_counter()
        try:
            result = await asyncio.wait_for(operation(), timeout=context.timeout_seconds)
            context.traces.append(WorkflowTraceEvent(context.workflow, name, reason_category, "succeeded", (time.perf_counter() - started) * 1000, provider=provider, model=model, decision_summary=f"Completed {name}."))
            return result
        except asyncio.TimeoutError as exc:
            context.traces.append(WorkflowTraceEvent(context.workflow, name, reason_category, "failed", (time.perf_counter() - started) * 1000, error_classification=ErrorCode.WORKFLOW_FAILED, decision_summary=f"{name} exceeded its timeout."))
            raise ChronosError(ErrorCode.WORKFLOW_FAILED, "The workflow timed out safely.") from exc
