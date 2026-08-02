import asyncio

import pytest
from pydantic import BaseModel

from app.core.errors import ChronosError, ErrorCode
from app.models.fake import FakeModelGateway
from app.models.gateway import ModelRequest, ToolPlan
from app.workflows.runtime import WorkflowRunner
from app.workflows.tools import PermissionClass, ToolRegistry, ToolSpec
from tests.fakes import MemoryTraces


class ValueInput(BaseModel):
    value: int


class ValueResult(BaseModel):
    doubled: int


def tool(permission=PermissionClass.INTERNAL_READ, *, handler=None, idempotent=True):
    async def default_handler(value: ValueInput): return ValueResult(doubled=value.value * 2)
    return ToolSpec(name="double", description="Double a validated number.", input_type=ValueInput, result_type=ValueResult, permission=permission, timeout_seconds=.05, idempotent=idempotent, audit_category="test", handler=handler or default_handler)


def runner(permission=PermissionClass.INTERNAL_READ, *, max_steps=3, budget=3, traces=None, handler=None):
    registry = ToolRegistry(); registry.register(tool(permission, handler=handler))
    return WorkflowRunner(max_steps=max_steps, timeout_seconds=.1, request_budget=budget, trace_repository=traces, tool_registry=registry)


def run(coro): return asyncio.run(coro)


def test_step_limit_is_enforced_and_traced():
    r = runner(max_steps=1); context = r.context("u", "test")
    run(r.run_step(context, "one", "deterministic", lambda: asyncio.sleep(0)))
    with pytest.raises(ChronosError): run(r.run_step(context, "two", "deterministic", lambda: asyncio.sleep(0)))
    assert context.traces[-1].decision_summary == "Workflow stopped at its safe step limit."


def test_request_budget_is_enforced_before_operation():
    r = runner(budget=1); context = r.context("u", "test")
    run(r.run_step(context, "model", "model", lambda: asyncio.sleep(0), request_units=1))
    with pytest.raises(ChronosError, match="request budget"): run(r.run_step(context, "tool", "tool", lambda: asyncio.sleep(0), request_units=1))
    assert context.request_count == 1


def test_per_step_timeout_is_traced():
    r = runner(); context = r.context("u", "test")
    with pytest.raises(ChronosError, match="timed out"): run(r.run_step(context, "slow", "tool", lambda: asyncio.sleep(.2), timeout_seconds=.01))
    assert context.traces[-1].error_classification == ErrorCode.WORKFLOW_FAILED


def test_unknown_tool_is_rejected():
    r = runner(); context = r.context("u", "test")
    with pytest.raises(ChronosError, match="unavailable tool"): run(r.execute_tool(context, ToolPlan("missing", {}, "test", "fake", "fake")))
    assert context.traces[-1].validation_result == "invalid"


def test_invalid_tool_arguments_are_rejected():
    r = runner(); context = r.context("u", "test")
    with pytest.raises(ChronosError, match="invalid tool arguments"): run(r.execute_tool(context, ToolPlan("double", {"value": "no"}, "test", "fake", "fake")))


def test_read_only_tool_executes_without_approval():
    r = runner(); context = r.context("u", "test", idempotency_key="same-request")
    result = run(r.execute_tool(context, ToolPlan("double", {"value": 4}, "test", "fake", "fake")))
    assert result.doubled == 8
    assert context.traces[-1].idempotency_key == "same-request"


def test_internal_write_is_denied_without_approval():
    r = runner(PermissionClass.INTERNAL_WRITE); context = r.context("u", "test")
    with pytest.raises(ChronosError) as error: run(r.execute_tool(context, ToolPlan("double", {"value": 2}, "test", "fake", "fake")))
    assert error.value.code == ErrorCode.AUTHORIZATION
    assert context.traces[-1].outcome == "denied"


def test_internal_write_executes_with_explicit_approval():
    r = runner(PermissionClass.INTERNAL_WRITE); context = r.context("u", "test")
    assert run(r.execute_tool(context, ToolPlan("double", {"value": 2}, "test", "fake", "fake"), user_approved=True)).doubled == 4


def test_external_write_is_denied_without_explicit_approval():
    r = runner(PermissionClass.EXTERNAL_WRITE); context = r.context("u", "test")
    with pytest.raises(ChronosError): run(r.execute_tool(context, ToolPlan("double", {"value": 2}, "test", "fake", "fake"), internal_write_enabled=True))
    assert context.traces[-1].outcome == "denied"


def test_model_selection_validation_execution_and_trace_persistence_are_connected():
    traces = MemoryTraces(); r = runner(traces=traces, budget=2); context = r.context("u", "test", request_id="req-1")
    gateway = FakeModelGateway(tool_plan=ToolPlan("double", {"value": 3}, "validated choice", "fake", "deterministic"))
    result = run(r.select_and_execute(context, gateway, ModelRequest(prompt="double it")))
    r.complete(context, {"done": True})
    assert result.doubled == 6
    assert context.request_count == 2
    assert [event["step_name"] for event in traces.events] == ["select_tool", "double"]
    assert traces.runs[context.run_id]["status"] == "completed"


def test_unexpected_tool_failure_is_classified_and_persisted():
    async def explode(value): raise RuntimeError("sensitive raw failure")
    traces = MemoryTraces(); r = runner(traces=traces, handler=explode); context = r.context("u", "test")
    with pytest.raises(ChronosError, match="could not complete safely"): run(r.execute_tool(context, ToolPlan("double", {"value": 1}, "test", "fake", "fake")))
    r.fail(context, ChronosError(ErrorCode.WORKFLOW_FAILED, "safe"))
    assert traces.events[-1]["payload_json"]["error_classification"] == ErrorCode.WORKFLOW_FAILED
    assert "sensitive" not in str(traces.events)
    assert traces.runs[context.run_id]["status"] == "failed"
