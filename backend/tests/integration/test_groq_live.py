import os

import pytest

from app.models.groq import GroqModelGateway
from app.workflows.intake import IntakeWorkflow
from app.workflows.runtime import WorkflowRunner
from tests.fakes import MemoryTraces


@pytest.mark.integration
@pytest.mark.anyio
async def test_real_groq_structured_intake_manual_case():
    if os.getenv("RUN_GROQ_INTEGRATION") != "1":
        pytest.skip("RUN_GROQ_INTEGRATION=1 is required for the live Groq test.")
    required = ["GROQ_API_KEY", "GROQ_MODEL_FAST", "GROQ_MODEL_REASONING"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        pytest.skip(f"Live Groq credentials/models are missing: {', '.join(missing)}")
    gateway = GroqModelGateway(
        api_key=os.environ["GROQ_API_KEY"],
        base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        models={"fast": os.environ["GROQ_MODEL_FAST"], "reasoning": os.environ["GROQ_MODEL_REASONING"], "tool_use": os.getenv("GROQ_MODEL_TOOL_USE", os.environ["GROQ_MODEL_FAST"])},
        timeout=float(os.getenv("MODEL_REQUEST_TIMEOUT_SECONDS", "20")),
        max_retries=1,
    )
    workflow = IntakeWorkflow(gateway, WorkflowRunner(max_steps=3, timeout_seconds=45, request_budget=2, trace_repository=MemoryTraces()))
    text = "I need to finish the authentication regression fix before tomorrow afternoon, prepare slides for Monday, attend a team call at 4 PM, and submit my database assignment by Tuesday morning. The auth fix needs around an hour. I do not know how long the slides will take, and I am waiting for my teammate to send the screenshots."
    result, _ = await workflow.extract(user_id="00000000-0000-0000-0000-000000000001", text=text, timezone_name="Asia/Kolkata")
    assert len(result.drafts) >= 4
    assert any(item.kind == "event" for item in result.drafts)
    assert any(item.dependencies or item.kind == "dependency" for item in result.drafts)
    assert any(item.effort_confidence == "unknown" for item in result.drafts)
    assert len(result.questions) <= 3
