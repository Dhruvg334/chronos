from __future__ import annotations

import re
from datetime import datetime, timezone

from app.models.gateway import ModelGateway, ModelRequest
from app.core.versions import INTAKE_PROMPT_VERSION, SCHEMA_VERSION
from app.schemas.intake import ExtractedCommitment, IntakeResponse
from app.workflows.runtime import WorkflowRunner


_TEMPORAL_CUE = re.compile(r"\b(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|morning|afternoon|evening|tonight|before|by|at\s+\d)\b", re.I)


def validate_intake_output(result: IntakeResponse, source: str) -> IntakeResponse:
    """Apply deterministic provenance, uncertainty, and clarification limits."""
    source_lower = source.casefold()
    seen: set[str] = set()
    drafts: list[ExtractedCommitment] = []
    missing: set[str] = set()
    for draft in result.drafts[:12]:
        key = re.sub(r"\W+", " ", draft.title.casefold()).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        updates: dict = {}
        if draft.source_text and draft.source_text.casefold() not in source_lower:
            updates["source_text"] = None
            updates["confidence_score"] = min(draft.confidence_score, 0.6)
        supported_dependencies = []
        source_tokens = set(re.findall(r"[a-z0-9]+", source_lower))
        for item in draft.dependencies:
            tokens = {token for token in re.findall(r"[a-z0-9]+", item.casefold()) if len(token) > 2}
            if tokens and len(tokens & source_tokens) / len(tokens) >= 0.6:
                supported_dependencies.append(item)
        if supported_dependencies != draft.dependencies:
            updates["dependencies"] = supported_dependencies
        if draft.deadline_at and not _TEMPORAL_CUE.search(source):
            updates.update(deadline_at=None, deadline_precision="none", confidence_score=min(draft.confidence_score, 0.6))
        if draft.estimated_minutes is None:
            updates["effort_confidence"] = "unknown"
        if draft.type == "event":
            updates["kind"] = "event"
        elif draft.type in {"habit", "recurring_obligation"}:
            updates["kind"] = "routine"
        elif draft.type == "waiting_on" or draft.dependencies:
            updates["kind"] = "dependency" if draft.type == "waiting_on" else draft.kind
        normalized = draft.model_copy(update=updates)
        missing.update(normalized.missing_fields)
        drafts.append(normalized)

    questions = []
    seen_questions: set[str] = set()
    for question in result.questions:
        key = question.question.casefold().strip()
        if key in seen_questions:
            continue
        if question.field not in missing:
            continue
        seen_questions.add(key)
        questions.append(question)
        if len(questions) == 3:
            break
    return result.model_copy(update={"drafts": drafts, "questions": questions})


class IntakeWorkflow:
    def __init__(self, gateway: ModelGateway, runner: WorkflowRunner):
        self.gateway = gateway
        self.runner = runner

    async def extract(self, *, user_id: str, text: str, timezone_name: str = "UTC", request_id: str | None = None) -> tuple[IntakeResponse, object]:
        context = self.runner.context(user_id, "intake", input_summary={"text_length": len(text)}, request_id=request_id)
        request = ModelRequest(
            prompt=(
                "Extract every distinct outcome. Classify each as event, task, routine, project_outcome, or dependency, "
                "while using storage types hard_deadline, soft_deadline, event, habit, waiting_on, recurring_obligation, reference, or someday. "
                "Preserve short supporting wording in source_text. Mark ambiguous deadline windows and unknown or approximate effort. "
                "Represent blockers as dependencies and ask at most three questions, only when a missing field materially changes planning. "
                "Never invent dates, durations, dependency deadlines, or facts. "
                f"Current time is {datetime.now(timezone.utc).isoformat()} and the user's timezone is {timezone_name}.\n\n"
                f"User text:\n{text}"
            ),
            system_prompt="You convert planning input into reviewable drafts. Never authorize or execute an external action.",
            model_role="fast",
            max_tokens=4000,
            temperature=0,
            prompt_version=INTAKE_PROMPT_VERSION, schema_version=SCHEMA_VERSION,
        )
        try:
            response = await self.runner.run_step(
                context,
                "extract_commitments",
                "structured_extraction",
                lambda: self.gateway.generate_structured(request, IntakeResponse),
                provider=self.gateway.metadata().get("provider"),
                model=self.gateway.metadata().get("fast_model") or self.gateway.metadata().get("model"),
                request_units=2,
                prompt_version=request.prompt_version,
                schema_version=request.schema_version,
                temperature=request.temperature,
            )
            validated = validate_intake_output(response.value, text)
            self.runner.complete(context, {"draft_count": len(validated.drafts), "question_count": len(validated.questions)})
            return validated, context
        except Exception as exc:
            self.runner.fail(context, exc)
            raise
