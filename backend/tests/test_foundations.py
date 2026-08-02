import asyncio

from fastapi.testclient import TestClient

from app.main import app
from app.models.fake import FakeModelGateway
from app.models.gateway import ModelRequest, ProviderHealth
from app.strategies.models import StrategyContext, StrategyId
from app.strategies.selector import StrategySelector
from app.workflows.runtime import WorkflowRunner


def test_health_endpoints_do_not_require_services():
    client = TestClient(app)
    live = client.get("/api/v1/health/live")
    ready = client.get("/api/v1/health/ready")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"
    assert ready.status_code == 200
    assert ready.json()["dependencies"]["database"]["state"] == "unconfigured"
    assert "secret" not in ready.text.lower()


def test_fake_model_gateway_is_deterministic():
    gateway = FakeModelGateway(text="next action")
    response = asyncio.run(gateway.generate_text(ModelRequest(prompt="What next?")))
    health = asyncio.run(gateway.health())
    assert response.text == "next action"
    assert health.state == ProviderHealth.READY


def test_workflow_runner_records_observable_trace():
    runner = WorkflowRunner(max_steps=2, timeout_seconds=1, request_budget=1)
    context = runner.context("user", "example")

    async def operation(): return "done"

    assert asyncio.run(runner.run_step(context, "validate", "deterministic", operation)) == "done"
    assert context.traces[0].decision_summary == "Completed validate."


def test_strategy_selector_required_cases():
    selector = StrategySelector()
    assert selector.recommend(StrategyContext(task_title="Reply", estimate_minutes=2)).strategy == StrategyId.QUICK_ACTION
    assert selector.recommend(StrategyContext(similar_quick_tasks=3, deep_work_active=True)).strategy == StrategyId.BATCHING
    assert selector.recommend(StrategyContext(remaining_work_minutes=390, free_minutes=240, major_outcomes=1, short_tasks=5, maintenance_tasks=4)).strategy == StrategyId.CONSTRAINED_DAY
    assert selector.recommend(StrategyContext(urgent=True, important=True, deadline_minutes=90, remaining_work_minutes=45)).strategy == StrategyId.EISENHOWER
    assert selector.recommend(StrategyContext(recurring=True, recent_completions=5, missed_yesterday=True)).strategy == StrategyId.CONTINUITY


def test_energy_recommendation_requires_evidence():
    assert StrategySelector().recommend(StrategyContext(energy_samples=0, energy_confidence=0)) is None
