from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.core.errors import ChronosError, ErrorCode
from app.models.gateway import ModelGateway, ModelRequest
from app.repositories.protocols import RepositorySet
from app.schemas.adaptive import (
    AdaptivePlanResponse,
    CandidatePlan,
    PlanExplanation,
    PlanningModelOutput,
    ValidatedPlan,
)
from app.schemas.planning_profile import PlanningProfile
from app.services.core_journey import CoreJourneyService, parse_datetime, rank_commitments
from app.workflows.runtime import WorkflowRunner


def _overlaps(start: datetime, end: datetime, other_start: datetime, other_end: datetime) -> bool:
    return start < other_end and end > other_start


class AdaptivePlanningWorkflow:
    """One model diagnosis followed by deterministic candidate validation."""

    def __init__(self, gateway: ModelGateway, runner: WorkflowRunner, repositories: RepositorySet):
        self.gateway = gateway
        self.runner = runner
        self.repositories = repositories

    @staticmethod
    def validate_candidate(
        candidate: CandidatePlan,
        *,
        commitments: dict[str, dict[str, Any]],
        events: list[dict[str, Any]],
        existing_blocks: list[dict[str, Any]],
        profile: PlanningProfile,
        range_start: datetime,
        range_end: datetime,
        remaining_capacity: int,
    ) -> ValidatedPlan | None:
        zone = ZoneInfo(profile.timezone)
        proposed: list[tuple[datetime, datetime]] = []
        total = 0
        for block in candidate.blocks:
            commitment = commitments.get(block.commitment_id)
            if not commitment or commitment.get("status") == "blocked" or commitment.get("type") == "waiting_on":
                return None
            start = block.start_at if block.start_at.tzinfo else block.start_at.replace(tzinfo=zone)
            end = start + timedelta(minutes=block.duration_minutes)
            if start < range_start or end > range_end:
                return None
            local_start, local_end = start.astimezone(zone), end.astimezone(zone)
            if local_start.date() != local_end.date() or local_start.weekday() not in profile.available_weekdays:
                return None
            if local_start.time() < profile.working_start_time or local_end.time() > profile.working_end_time:
                return None
            if (
                profile.protected_interval_start
                and profile.protected_interval_end
                and local_start.time() < profile.protected_interval_end
                and local_end.time() > profile.protected_interval_start
            ):
                return None
            if commitment.get("deadline_at") and end > parse_datetime(commitment["deadline_at"]):
                return None
            buffer = timedelta(minutes=profile.minimum_transition_buffer_minutes)
            for row in [*events, *existing_blocks]:
                if row.get("status") in {"skipped", "moved"}:
                    continue
                if _overlaps(start - buffer, end + buffer, parse_datetime(row["start_at"]), parse_datetime(row["end_at"])):
                    return None
            if any(_overlaps(start - buffer, end + buffer, other_start, other_end) for other_start, other_end in proposed):
                return None
            proposed.append((start, end))
            total += block.duration_minutes
        if total > remaining_capacity:
            return None
        return ValidatedPlan(**candidate.model_dump(), feasibility="valid")

    async def recommend(
        self,
        *,
        user_id: str,
        start_at: datetime,
        end_at: datetime,
        request_id: str | None = None,
    ) -> AdaptivePlanResponse:
        context = self.runner.context(
            user_id,
            "adaptive_planning",
            input_summary={"range_hours": round((end_at - start_at).total_seconds() / 3600, 1)},
            request_id=request_id,
        )
        try:
            service = CoreJourneyService(self.repositories)
            current_plan = service.plan(user_id, start_at, end_at)
            ranked = rank_commitments(self.repositories.commitments.list_for_user(user_id))
            commitments = {str(item["id"]): item for item in ranked}
            compact_context = {
                "timezone": current_plan.timezone,
                "range": [start_at.isoformat(), end_at.isoformat()],
                "capacity": current_plan.capacity.model_dump(),
                "commitments": [
                    {
                        "id": str(item["id"]),
                        "title": item["title"],
                        "type": item.get("type"),
                        "status": item.get("status"),
                        "deadline_at": item.get("deadline_at"),
                        "remaining_minutes": max(0, int(item.get("estimated_minutes") or 0) - int(item.get("actual_minutes") or 0)),
                        "importance": item.get("importance"),
                        "risk_level": item.get("risk_level"),
                    }
                    for item in ranked[:12]
                ],
                "calendar": [item.model_dump(mode="json") for item in current_plan.calendar_events],
                "current_blocks": [item.model_dump(mode="json") for item in current_plan.plan_blocks],
            }
            request = ModelRequest(
                prompt=(
                    "Diagnose the planning conflicts and return one to three small candidate plans. "
                    "Use only supplied commitment IDs. Do not schedule blocked or waiting_on work. "
                    "Respect the supplied timezone, calendar, working limits, and capacity; deterministic validation will reject violations. "
                    f"Context: {json.dumps(compact_context, default=str, separators=(',', ':'))}"
                ),
                system_prompt="Propose reviewable plans only. Do not mutate data or reveal hidden reasoning.",
                model_role="reasoning",
                temperature=0,
                metadata={"workflow_id": context.workflow_id},
            )
            response = await self.runner.run_step(
                context,
                "diagnose_and_propose",
                "model_planning",
                lambda: self.gateway.generate_structured(request, PlanningModelOutput),
                provider=self.gateway.metadata().get("provider"),
                model=self.gateway.metadata().get("reasoning_model") or self.gateway.metadata().get("model"),
                request_units=2,
            )
            profile = PlanningProfile.model_validate(self.repositories.planning_profiles.get(user_id))
            events = self.repositories.planning.list_calendar_events(user_id, start_at, end_at)
            blocks = self.repositories.focus.list_for_user(user_id, start_at, end_at)
            valid = [
                validated
                for candidate in response.value.candidates
                if (validated := self.validate_candidate(
                    candidate,
                    commitments=commitments,
                    events=events,
                    existing_blocks=blocks,
                    profile=profile,
                    range_start=start_at,
                    range_end=end_at,
                    remaining_capacity=current_plan.capacity.remaining_minutes,
                ))
            ]
            if not valid:
                raise ChronosError(ErrorCode.VALIDATION, "No proposed plan fit your availability and constraints.")
            rank_index = {str(item["id"]): index for index, item in enumerate(ranked)}
            selected = min(
                valid,
                key=lambda plan: (
                    min(rank_index.get(block.commitment_id, 999) for block in plan.blocks),
                    len(plan.deferred_commitment_ids),
                    sum(block.duration_minutes for block in plan.blocks),
                    plan.label,
                ),
            )
            proposal = self.repositories.planning.create_proposal(user_id, {
                "id": str(uuid.uuid4()),
                "agent_run_id": context.run_id,
                "action_type": "commitment_reschedule",
                "status": "pending",
                "payload_json": {"adaptive_plan": selected.model_dump(mode="json"), "planning_range": [start_at.isoformat(), end_at.isoformat()], "requires_approval": True},
                "explanation": "Model-assisted proposal validated against availability, calendar, dependencies, overlap, and capacity. No plan data changed.",
            })
            selected_ids = {block.commitment_id for block in selected.blocks}
            explanation = PlanExplanation(
                constraints_considered=["personal availability", current_plan.capacity.calendar_state.replace("_", " "), "transition buffers", "capacity", "deadlines", "dependencies"],
                next_action_reason=f"{selected.blocks[0].rationale}",
                deferred=[str(item["title"]) for item in ranked if str(item["id"]) not in selected_ids][:4],
                changed="A proposal was prepared for review; the plan itself was not changed.",
                ai_used=True,
            )
            self.runner.complete(context, {"valid_candidates": len(valid), "rejected_candidates": len(response.value.candidates) - len(valid), "proposal_id": proposal["id"]})
            return AdaptivePlanResponse(
                workflow_id=context.workflow_id,
                proposal_id=str(proposal["id"]),
                recommended_plan=selected,
                explanation=explanation,
                rejected_candidate_count=len(response.value.candidates) - len(valid),
            )
        except Exception as exc:
            self.runner.fail(context, exc)
            raise
