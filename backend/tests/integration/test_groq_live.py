from __future__ import annotations

import logging
import os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.core.config import settings
from app.core.errors import ChronosError, ErrorCode
from app.models.gateway import ModelRequest
from app.models.groq import GroqModelGateway
from app.schemas.adaptive import PlanningModelOutput, RecoveryModelOutput
from app.schemas.planning_profile import PlanningProfile
from app.workflows.adaptive_planning import AdaptivePlanningWorkflow
from app.workflows.intake import IntakeWorkflow
from app.workflows.runtime import WorkflowRunner
from tests.fakes import MemoryTraces


pytestmark = [pytest.mark.integration, pytest.mark.anyio]
USER_ID = "00000000-0000-0000-0000-000000000001"
MANUAL_TEXT = (
    "I need to finish the authentication regression fix before tomorrow afternoon, prepare slides for Monday, "
    "attend a team call at 4 PM, and submit my database assignment by Tuesday morning. The auth fix needs around "
    "an hour. I do not know how long the slides will take, and I am waiting for my teammate to send the screenshots."
)


def _live_gateway() -> GroqModelGateway:
    if os.getenv("RUN_GROQ_INTEGRATION") != "1":
        pytest.skip("RUN_GROQ_INTEGRATION=1 is required for live Groq tests.")
    missing = [
        name
        for name, value in {
            "GROQ_API_KEY": settings.GROQ_API_KEY,
            "GROQ_MODEL_FAST": settings.GROQ_MODEL_FAST,
            "GROQ_MODEL_REASONING": settings.GROQ_MODEL_REASONING,
            "GROQ_MODEL_TOOL_USE": settings.GROQ_MODEL_TOOL_USE,
        }.items()
        if not value
    ]
    if missing:
        pytest.fail(f"Live Groq settings are missing: {', '.join(missing)}")
    return GroqModelGateway.from_settings(settings)


async def test_real_groq_structured_intake_and_metadata():
    gateway = _live_gateway()
    traces = MemoryTraces()
    workflow = IntakeWorkflow(
        gateway,
        WorkflowRunner(max_steps=3, timeout_seconds=settings.WORKFLOW_TIMEOUT_SECONDS, request_budget=2, trace_repository=traces),
    )
    result, context = await workflow.extract(user_id=USER_ID, text=MANUAL_TEXT, timezone_name="Asia/Kolkata")
    assert len(result.drafts) >= 4
    assert any(item.kind == "event" for item in result.drafts)
    assert any(item.dependencies or item.kind == "dependency" for item in result.drafts)
    assert any(item.effort_confidence == "unknown" for item in result.drafts)
    assert len(result.questions) <= 3
    assert context.request_count == 2
    metadata = gateway.metadata()
    assert metadata["provider"] == "groq"
    assert metadata["fast_model"] == settings.GROQ_MODEL_FAST
    assert traces.runs[context.run_id]["status"] == "completed"


async def test_real_groq_planning_candidates_are_deterministically_filtered():
    gateway = _live_gateway()
    zone = ZoneInfo("Asia/Kolkata")
    day = datetime.now(zone).date() + timedelta(days=1)
    while day.weekday() > 5:
        day += timedelta(days=1)
    at = lambda value: datetime.combine(day, value, zone)
    prompt = (
        f"Return exactly two candidate plans for commitment c1. Candidate one must start at {at(time(10)).isoformat()} "
        f"for 30 minutes. Candidate two must start at {at(time(13, 15)).isoformat()} for 30 minutes. Use commitment_id c1, "
        "include concise rationale/summary text, and no other blocks. The second candidate intentionally overlaps "
        "the protected 13:00-14:00 interval so deterministic validation can reject it."
    )
    response = await gateway.generate_structured(
        ModelRequest(prompt=prompt, system_prompt="Return reviewable candidate plans only.", model_role="reasoning", temperature=0),
        PlanningModelOutput,
    )
    profile = PlanningProfile(
        timezone="Asia/Kolkata", available_weekdays=[0, 1, 2, 3, 4, 5],
        working_start_time=time(9, 30), working_end_time=time(18, 30),
        daily_focus_limit_minutes=300, minimum_transition_buffer_minutes=10,
        minimum_daily_unscheduled_buffer_minutes=60,
        protected_interval_start=time(13), protected_interval_end=time(14),
    )
    commitment = {
        "id": "c1", "title": "Authentication regression fix", "status": "active", "type": "hard_deadline",
        "deadline_at": (at(time(18)) + timedelta(days=1)).isoformat(),
    }
    accepted = [
        AdaptivePlanningWorkflow.validate_candidate(
            candidate,
            commitments={"c1": commitment}, events=[], existing_blocks=[], profile=profile,
            range_start=at(time(9, 30)), range_end=at(time(18, 30)), remaining_capacity=300,
        )
        for candidate in response.value.candidates
    ]
    assert response.provider == "groq" and response.model == settings.GROQ_MODEL_REASONING
    assert response.repair_attempts in {0, 1}
    assert len(response.value.candidates) == 2
    assert sum(item is not None for item in accepted) == 1


async def test_real_groq_recovery_options_are_bounded():
    gateway = _live_gateway()
    response = await gateway.generate_structured(
        ModelRequest(
            prompt=(
                "The deterministic diagnosis is dependency_blocked because screenshots have not arrived. Return one to three "
                "recovery options using only smaller_next_step, protect_short_block, or defer_lower_priority. Include rationale, "
                "trade-off, expected impact, required approval, and feasibility. Do not claim the dependency has a deadline."
            ),
            system_prompt="Recommend bounded recovery options only; do not take action.",
            model_role="reasoning",
            temperature=0,
        ),
        RecoveryModelOutput,
    )
    assert response.provider == "groq" and response.model == settings.GROQ_MODEL_REASONING
    assert response.value.diagnosis == "dependency_blocked"
    assert 1 <= len(response.value.options) <= 3
    normalized = [option.model_copy(update={"required_approval": True}) for option in response.value.options]
    assert all(option.required_approval for option in normalized)


async def test_real_groq_provider_error_is_safely_classified_and_redacted(caplog):
    _live_gateway()
    sentinel = "LIVE_RAW_PROMPT_SENTINEL_DO_NOT_LOG"
    invalid_gateway = GroqModelGateway(
        api_key=settings.GROQ_API_KEY,
        base_url=settings.GROQ_BASE_URL,
        models={"fast": "chronos-intentionally-invalid-model", "reasoning": settings.GROQ_MODEL_REASONING, "tool_use": settings.GROQ_MODEL_TOOL_USE},
        timeout=settings.MODEL_REQUEST_TIMEOUT_SECONDS,
        max_retries=0,
    )
    with caplog.at_level(logging.INFO), pytest.raises(ChronosError) as raised:
        await invalid_gateway.generate_text(ModelRequest(prompt=sentinel, model_role="fast"))
    assert raised.value.code == ErrorCode.EXTERNAL_UNAVAILABLE
    assert settings.GROQ_API_KEY not in caplog.text
    assert sentinel not in caplog.text
    assert "invalid_request_error" not in caplog.text
