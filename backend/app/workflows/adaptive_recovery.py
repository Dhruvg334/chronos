from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from app.core.errors import ChronosError, ErrorCode
from app.models.gateway import ModelGateway, ModelRequest
from app.repositories.protocols import RepositorySet
from app.schemas.adaptive import AdaptiveRecoveryResponse, RecoveryCause, RecoveryModelOutput, RecoveryOption
from app.schemas.planning_profile import PlanningProfile
from app.services.core_journey import CoreJourneyService, parse_datetime
from app.workflows.runtime import WorkflowRunner


def diagnose_recovery(commitment: dict[str, Any], reflections: list[dict[str, Any]], *, over_capacity: int, calendar_state: str) -> RecoveryCause:
    if commitment.get("status") == "blocked" or commitment.get("type") == "waiting_on":
        return "dependency_blocked"
    if not commitment.get("description") or float(commitment.get("confidence_score") or 0) < 0.6:
        return "ambiguity"
    if over_capacity > 0:
        return "overload"
    if calendar_state in {"stale", "unavailable"}:
        return "calendar_disruption"
    actual = int(commitment.get("actual_minutes") or 0)
    estimate = int(commitment.get("estimated_minutes") or 0)
    if estimate and actual > estimate and float(commitment.get("progress_percent") or 0) < 100:
        return "underestimated_duration"
    energy = [int(row["energy_level"]) for row in reflections if row.get("energy_level") is not None]
    if len(energy) >= 3 and sum(energy) / len(energy) <= 2:
        return "low_available_energy"
    if any("interrupt" in str(row.get("blocker_reason") or "").casefold() for row in reflections):
        return "interruption"
    return "avoidance_start_friction"


class AdaptiveRecoveryWorkflow:
    def __init__(self, gateway: ModelGateway, runner: WorkflowRunner, repositories: RepositorySet):
        self.gateway = gateway
        self.runner = runner
        self.repositories = repositories

    def _first_focus_slot(self, user_id: str, profile: PlanningProfile, duration: int) -> tuple[datetime, datetime] | None:
        zone = ZoneInfo(profile.timezone)
        now = datetime.now(timezone.utc).astimezone(zone)
        buffer = timedelta(minutes=profile.minimum_transition_buffer_minutes)
        for offset in range(7):
            day = now.date() + timedelta(days=offset)
            if day.weekday() not in profile.available_weekdays:
                continue
            cursor = datetime.combine(day, profile.working_start_time, zone)
            if day == now.date():
                rounded = now.replace(second=0, microsecond=0) + timedelta(minutes=(10 - now.minute % 10) % 10)
                cursor = max(cursor, rounded)
            end_of_work = datetime.combine(day, profile.working_end_time, zone)
            events = self.repositories.planning.list_calendar_events(user_id, cursor - buffer, end_of_work + buffer)
            blocks = self.repositories.focus.list_for_user(user_id, cursor - buffer, end_of_work + buffer)
            while cursor + timedelta(minutes=duration) <= end_of_work:
                end = cursor + timedelta(minutes=duration)
                if profile.protected_interval_start and profile.protected_interval_end:
                    protected_start = datetime.combine(day, profile.protected_interval_start, zone)
                    protected_end = datetime.combine(day, profile.protected_interval_end, zone)
                    if cursor < protected_end and end > protected_start:
                        cursor = protected_end + buffer
                        continue
                if not any(parse_datetime(row["start_at"]) < end + buffer and parse_datetime(row["end_at"]) > cursor - buffer for row in [*events, *blocks] if row.get("status") not in {"skipped", "moved"}):
                    return cursor, end
                cursor += timedelta(minutes=10)
        return None

    async def recommend(self, *, user_id: str, commitment_id: str, request_id: str | None = None) -> AdaptiveRecoveryResponse:
        commitment = self.repositories.commitments.get_for_user(user_id, commitment_id)
        if not commitment:
            raise ChronosError(ErrorCode.VALIDATION, "Commitment not found.")
        context = self.runner.context(user_id, "adaptive_recovery", input_summary={"commitment_id": commitment_id}, request_id=request_id)
        try:
            service = CoreJourneyService(self.repositories)
            now = datetime.now(timezone.utc)
            plan = service.plan(user_id, now.replace(hour=0, minute=0, second=0, microsecond=0), now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1))
            reflections = self.repositories.reflections.list_recent(user_id, commitment_id)
            diagnosis = diagnose_recovery(commitment, reflections, over_capacity=plan.capacity.over_capacity_minutes, calendar_state=plan.capacity.calendar_state)
            compact = {
                "commitment": {key: commitment.get(key) for key in ("id", "title", "type", "status", "estimated_minutes", "actual_minutes", "progress_percent", "risk_level", "confidence_score")},
                "deterministic_diagnosis": diagnosis,
                "capacity": plan.capacity.model_dump(),
                "recent_observations": [{"completion_status": row.get("completion_status"), "energy_level": row.get("energy_level"), "blocker_category": "interruption" if "interrupt" in str(row.get("blocker_reason") or "").casefold() else "other"} for row in reflections[:5]],
            }
            request = ModelRequest(
                prompt=(
                    "Return at most three concise recovery options using only the allowed actions. "
                    "Treat the deterministic diagnosis as authoritative and make trade-offs explicit. "
                    f"Context: {json.dumps(compact, default=str, separators=(',', ':'))}"
                ),
                system_prompt="Recommend recovery actions only. Do not mutate plans, contact people, or reveal hidden reasoning.",
                model_role="reasoning",
                temperature=0,
                metadata={"workflow_id": context.workflow_id},
            )
            ai_used = True
            try:
                response = await self.runner.run_step(
                    context,
                    "diagnose_recovery",
                    "model_recovery",
                    lambda: self.gateway.generate_structured(request, RecoveryModelOutput),
                    provider=self.gateway.metadata().get("provider"),
                    model=self.gateway.metadata().get("reasoning_model") or self.gateway.metadata().get("model"),
                    request_units=2,
                )
                model_options = response.value.options
            except ChronosError as exc:
                if exc.code not in {ErrorCode.CONFIGURATION, ErrorCode.EXTERNAL_UNAVAILABLE, ErrorCode.RATE_LIMITED, ErrorCode.MODEL_OUTPUT_INVALID}:
                    raise
                ai_used = False
                model_options = [RecoveryOption(
                    action="smaller_next_step" if diagnosis != "dependency_blocked" else "defer_lower_priority",
                    rationale="Reduce the immediate commitment to one clear, executable decision.",
                    trade_off="The full outcome may move later while uncertainty or constraints are resolved.",
                    expected_impact="Creates a credible next step without silently changing the plan.",
                    required_approval=True,
                    feasible=True,
                    feasibility_reason="This recommendation does not require an unavailable calendar slot.",
                )]
            profile = PlanningProfile.model_validate(self.repositories.planning_profiles.get(user_id))
            options: list[RecoveryOption] = []
            focus_slot = self._first_focus_slot(user_id, profile, min(profile.default_focus_duration_minutes, 45))
            for option in model_options[:3]:
                feasible = option.feasible
                reason = option.feasibility_reason
                if diagnosis == "dependency_blocked" and option.action == "protect_short_block":
                    feasible, reason = False, "Blocked work is not executable until its dependency clears."
                elif option.action == "protect_short_block" and not focus_slot:
                    feasible, reason = False, "No conflict-free slot fits the current availability window."
                options.append(option.model_copy(update={"feasible": feasible, "feasibility_reason": reason, "required_approval": True}))
            proposals = []
            for option in options:
                payload: dict[str, Any] = {
                    "rescue_action_type": {"smaller_next_step": "compress_scope", "protect_short_block": "create_rescue_focus_block", "defer_lower_priority": "defer_lower_priority"}[option.action],
                    "commitment_id": commitment_id,
                    "title": f"Recovery for {commitment['title']}",
                    "rationale": option.rationale,
                    "trade_off": option.trade_off,
                    "expected_impact": option.expected_impact,
                    "required_approval": True,
                    "feasible": option.feasible,
                    "feasibility_reason": option.feasibility_reason,
                    "diagnosis": diagnosis,
                }
                if option.action == "protect_short_block" and focus_slot:
                    payload.update(start_at=focus_slot[0].isoformat(), end_at=focus_slot[1].isoformat())
                proposal = self.repositories.planning.create_proposal(user_id, {
                    "id": str(uuid.uuid4()), "agent_run_id": context.run_id, "action_type": "commitment_rescue", "status": "pending",
                    "payload_json": payload,
                    "explanation": "This recovery option was model-assisted and deterministically checked. No plan data changes until approval.",
                })
                proposals.append(proposal)
            self.runner.complete(context, {"diagnosis": diagnosis, "proposal_count": len(proposals), "ai_used": ai_used})
            return AdaptiveRecoveryResponse(workflow_id=context.workflow_id, diagnosis=diagnosis, proposals=proposals, ai_used=ai_used)
        except Exception as exc:
            self.runner.fail(context, exc)
            raise
