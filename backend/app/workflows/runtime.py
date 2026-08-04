from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from pydantic import ValidationError

from app.core.errors import ChronosError, ErrorCode
from app.models.gateway import ModelGateway, ModelRequest, ToolDefinition, ToolPlan
from app.repositories.protocols import WorkflowTraceRepository
from app.workflows.approval import RecommendationFirstApprovalPolicy
from app.workflows.tools import ToolRegistry
from app.core.versions import TOOL_SELECTION_POLICY_VERSION


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
    request_id: str | None = None
    workflow_id: str | None = None
    idempotency_key: str | None = None
    prompt_version: str | None = None
    schema_version: str | None = None
    temperature: float | None = None
    request_count: int = 0
    token_usage: dict[str, int] = field(default_factory=dict)
    repair_count: int = 0

    def persistence_payload(self) -> dict[str, Any]:
        return {
            "step_name": self.step,
            "tool_name": self.tool_selected,
            "status": self.outcome,
            "explanation": self.decision_summary,
            "payload_json": {
                "reason_category": self.reason_category,
                "validation_result": self.validation_result,
                "duration_ms": round(self.duration_ms, 2),
                "provider": self.provider,
                "model": self.model,
                "error_classification": self.error_classification,
                "request_id": self.request_id,
                "workflow_id": self.workflow_id,
                "idempotency_key": self.idempotency_key,
                "prompt_version": self.prompt_version,
                "schema_version": self.schema_version,
                "temperature": self.temperature,
                "request_count": self.request_count,
                "token_usage": self.token_usage,
                "repair_count": self.repair_count,
            },
        }


@dataclass
class WorkflowContext:
    workflow_id: str
    user_id: str
    workflow: str
    max_steps: int
    timeout_seconds: float
    request_budget: int
    run_id: str | None = None
    request_id: str | None = None
    idempotency_key: str | None = None
    step_count: int = 0
    request_count: int = 0
    traces: list[WorkflowTraceEvent] = field(default_factory=list)


class WorkflowRunner:
    def __init__(
        self,
        *,
        max_steps: int,
        timeout_seconds: float,
        request_budget: int,
        trace_repository: WorkflowTraceRepository | None = None,
        tool_registry: ToolRegistry | None = None,
        approval_policy: RecommendationFirstApprovalPolicy | None = None,
    ):
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds
        self.request_budget = request_budget
        self.trace_repository = trace_repository
        self.tool_registry = tool_registry or ToolRegistry()
        self.approval_policy = approval_policy or RecommendationFirstApprovalPolicy()

    def context(
        self,
        user_id: str,
        workflow: str,
        *,
        input_summary: dict[str, Any] | None = None,
        request_id: str | None = None,
        workflow_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> WorkflowContext:
        resolved_id = workflow_id or str(uuid.uuid4())
        run_id = None
        if self.trace_repository is not None:
            run_id = self.trace_repository.create_run(
                user_id,
                workflow,
                input_summary or {},
                workflow_id=resolved_id,
            )
        return WorkflowContext(
            resolved_id,
            user_id,
            workflow,
            self.max_steps,
            self.timeout_seconds,
            self.request_budget,
            run_id=run_id,
            request_id=request_id,
            idempotency_key=idempotency_key,
        )

    def _record(self, context: WorkflowContext, event: WorkflowTraceEvent) -> None:
        event.workflow_id = context.workflow_id
        event.request_id = context.request_id
        event.idempotency_key = context.idempotency_key
        context.traces.append(event)
        if self.trace_repository is not None and context.run_id is not None:
            self.trace_repository.append(context.user_id, context.run_id, event.persistence_payload())

    def _guard(self, context: WorkflowContext, name: str, reason_category: str, request_units: int) -> None:
        if context.step_count >= context.max_steps:
            self._record(context, WorkflowTraceEvent(context.workflow, name, reason_category, "failed", 0, error_classification=ErrorCode.WORKFLOW_FAILED, decision_summary="Workflow stopped at its safe step limit."))
            raise ChronosError(ErrorCode.WORKFLOW_FAILED, "This workflow reached its safe step limit.")
        if request_units < 0 or context.request_count + request_units > context.request_budget:
            self._record(context, WorkflowTraceEvent(context.workflow, name, reason_category, "failed", 0, error_classification=ErrorCode.WORKFLOW_FAILED, decision_summary="Workflow stopped at its model and tool request budget."))
            raise ChronosError(ErrorCode.WORKFLOW_FAILED, "This workflow reached its safe request budget.")
        context.step_count += 1
        context.request_count += request_units

    async def run_step(
        self,
        context: WorkflowContext,
        name: str,
        reason_category: str,
        operation: Callable[[], Awaitable[Any]],
        *,
        provider: str | None = None,
        model: str | None = None,
        request_units: int = 0,
        timeout_seconds: float | None = None,
        tool_selected: str | None = None,
        prompt_version: str | None = None,
        schema_version: str | None = None,
        temperature: float | None = None,
    ) -> Any:
        self._guard(context, name, reason_category, request_units)
        started = time.perf_counter()
        try:
            result = await asyncio.wait_for(operation(), timeout=min(timeout_seconds or context.timeout_seconds, context.timeout_seconds))
            self._record(context, WorkflowTraceEvent(context.workflow, name, reason_category, "succeeded", (time.perf_counter() - started) * 1000,
                tool_selected=tool_selected, provider=getattr(result, "provider", provider), model=getattr(result, "model", model),
                decision_summary=f"Completed {name}.", prompt_version=(prompt_version if getattr(result, "prompt_version", "unspecified") == "unspecified" else result.prompt_version),
                schema_version=(schema_version if getattr(result, "schema_version", "unspecified") == "unspecified" else result.schema_version), temperature=temperature,
                request_count=getattr(result, "request_count", request_units), token_usage=getattr(result, "token_usage", {}),
                repair_count=getattr(result, "repair_attempts", 0)))
            return result
        except asyncio.TimeoutError as exc:
            self._record(context, WorkflowTraceEvent(context.workflow, name, reason_category, "failed", (time.perf_counter() - started) * 1000, tool_selected=tool_selected, error_classification=ErrorCode.WORKFLOW_FAILED, decision_summary=f"{name} exceeded its timeout."))
            raise ChronosError(ErrorCode.WORKFLOW_FAILED, "The workflow timed out safely.") from exc
        except ValidationError as exc:
            self._record(context, WorkflowTraceEvent(context.workflow, name, reason_category, "failed", (time.perf_counter() - started) * 1000, tool_selected=tool_selected, validation_result="invalid", error_classification=ErrorCode.VALIDATION, decision_summary=f"{name} failed schema validation."))
            raise ChronosError(ErrorCode.VALIDATION, "The workflow produced invalid data.") from exc
        except ChronosError as exc:
            self._record(context, WorkflowTraceEvent(context.workflow, name, reason_category, "failed", (time.perf_counter() - started) * 1000, tool_selected=tool_selected, error_classification=exc.code, decision_summary=f"{name} failed safely."))
            raise
        except Exception as exc:
            self._record(context, WorkflowTraceEvent(context.workflow, name, reason_category, "failed", (time.perf_counter() - started) * 1000, tool_selected=tool_selected, error_classification=ErrorCode.WORKFLOW_FAILED, decision_summary=f"{name} failed unexpectedly."))
            raise ChronosError(ErrorCode.WORKFLOW_FAILED, "The workflow could not complete safely.") from exc

    async def execute_tool(
        self,
        context: WorkflowContext,
        plan: ToolPlan,
        *,
        user_approved: bool = False,
        internal_write_enabled: bool = False,
    ) -> Any:
        started = time.perf_counter()
        try:
            tool = self.tool_registry.get(plan.tool_name or "")
        except ValueError as exc:
            self._guard(context, "tool_selection", "tool_validation", 0)
            self._record(context, WorkflowTraceEvent(context.workflow, "tool_selection", "tool_validation", "failed", (time.perf_counter() - started) * 1000, tool_selected=plan.tool_name, validation_result="invalid", error_classification=ErrorCode.VALIDATION, decision_summary="Rejected an unknown tool selection."))
            raise ChronosError(ErrorCode.VALIDATION, "The workflow selected an unavailable tool.") from exc

        try:
            validated_input = tool.validate_input(plan.arguments)
        except ValidationError as exc:
            self._guard(context, tool.name, "tool_validation", 0)
            self._record(context, WorkflowTraceEvent(context.workflow, tool.name, "tool_validation", "failed", (time.perf_counter() - started) * 1000, tool_selected=tool.name, validation_result="invalid", error_classification=ErrorCode.VALIDATION, decision_summary="Rejected invalid tool arguments."))
            raise ChronosError(ErrorCode.VALIDATION, "The workflow supplied invalid tool arguments.") from exc

        decision = self.approval_policy.evaluate(tool, user_approved=user_approved, internal_write_enabled=internal_write_enabled)
        if not decision.allowed:
            self._guard(context, tool.name, "approval", 0)
            self._record(context, WorkflowTraceEvent(context.workflow, tool.name, "approval", "denied", (time.perf_counter() - started) * 1000, tool_selected=tool.name, error_classification=ErrorCode.AUTHORIZATION, decision_summary=decision.reason))
            raise ChronosError(ErrorCode.AUTHORIZATION, decision.reason)

        async def invoke():
            raw_result = await tool.handler(validated_input)
            return tool.validate_result(raw_result)

        return await self.run_step(context, tool.name, "tool_execution", invoke, request_units=1, timeout_seconds=tool.timeout_seconds, tool_selected=tool.name)

    async def select_and_execute(
        self,
        context: WorkflowContext,
        gateway: ModelGateway,
        request: ModelRequest,
        *,
        user_approved: bool = False,
        internal_write_enabled: bool = False,
    ) -> Any:
        definitions = [ToolDefinition(tool.name, tool.description, tool.input_type.model_json_schema()) for tool in self.tool_registry.all()]
        metadata = gateway.metadata()
        plan = await self.run_step(
            context,
            "select_tool",
            "model_tool_selection",
            lambda: gateway.select_tools(request, definitions),
            provider=metadata.get("provider"),
            model=metadata.get("tool_model") or metadata.get("model"),
            request_units=1,
            prompt_version=request.prompt_version if request.prompt_version != "unspecified" else TOOL_SELECTION_POLICY_VERSION,
            schema_version=request.schema_version,
            temperature=request.temperature,
        )
        return await self.execute_tool(context, plan, user_approved=user_approved, internal_write_enabled=internal_write_enabled)

    def complete(self, context: WorkflowContext, output_summary: dict[str, Any] | None = None) -> None:
        if self.trace_repository is not None and context.run_id is not None:
            self.trace_repository.complete_run(context.user_id, context.run_id, output_summary)

    def fail(self, context: WorkflowContext, error: ChronosError | Exception) -> None:
        if self.trace_repository is not None and context.run_id is not None:
            code = error.code if isinstance(error, ChronosError) else ErrorCode.WORKFLOW_FAILED
            self.trace_repository.fail_run(context.user_id, context.run_id, str(code))
