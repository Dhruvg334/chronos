from __future__ import annotations

from app.models.gateway import ModelGateway, ModelRequest
from app.schemas.intake import IntakeResponse
from app.workflows.runtime import WorkflowRunner


class IntakeWorkflow:
    def __init__(self, gateway: ModelGateway, runner: WorkflowRunner):
        self.gateway = gateway
        self.runner = runner

    async def extract(self, *, user_id: str, text: str) -> tuple[IntakeResponse, list]:
        context = self.runner.context(user_id, "intake")
        request = ModelRequest(
            prompt=(
                "Extract distinct commitments, child tasks, and only necessary clarifying questions from this text. "
                "Use commitment types hard_deadline, soft_deadline, event, habit, waiting_on, "
                "recurring_obligation, reference, or someday. Make uncertainty explicit.\n\n"
                f"User text:\n{text}"
            ),
            system_prompt="You convert planning input into reviewable drafts. Never authorize or execute an external action.",
            model_role="fast",
            temperature=0,
        )
        response = await self.runner.run_step(
            context,
            "extract_commitments",
            "structured_extraction",
            lambda: self.gateway.generate_structured(request, IntakeResponse),
            provider=self.gateway.metadata().get("provider"),
            model=self.gateway.metadata().get("fast_model") or self.gateway.metadata().get("model"),
        )
        return response.value, context.traces
