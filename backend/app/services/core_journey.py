from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from app.core.errors import ChronosError, ErrorCode
from app.core.config import settings
from app.repositories.protocols import RepositorySet
from app.schemas.core import (
    ActiveFocusView,
    CapacityView,
    NextActionView,
    PlanItemView,
    PlanResponse,
    RecoveryView,
    TodayResponse,
)
from app.strategies.models import StrategyContext, StrategyId, StrategyPreferences
from app.strategies.selector import StrategySelector
from app.schemas.planning_profile import PlanningProfile
from app.services.capacity_engine import CapacityEngine, CapacityResult

ACTIVE_COMMITMENT_STATUSES = {"inbox", "clarified", "planned", "active", "blocked", "at_risk", "rescue"}
RISK_WEIGHT = {"rescue_required": 5, "critical": 4, "at_risk": 3, "watch": 2, "stable": 1}


def risk_level(score: float) -> str:
    if score < 25: return "stable"
    if score < 50: return "watch"
    if score < 75: return "at_risk"
    if score < 90: return "critical"
    return "rescue_required"


def calculate_core_risk(*, current_time: datetime, deadline_at: datetime | None, estimated_minutes: int | None, progress_percent: float, importance: int, flexibility: int, confidence_score: float) -> tuple[float, str, list[str]]:
    warnings: list[str] = []
    if not deadline_at or not estimated_minutes:
        if not deadline_at: warnings.append("Deadline is uncertain.")
        if not estimated_minutes: warnings.append("Effort is uncertain.")
        return 40.0, "watch", warnings
    minutes_until = int((deadline_at - current_time).total_seconds() // 60)
    if minutes_until <= 0 and progress_percent < 100:
        return 100.0, "rescue_required", ["The deadline has passed."]
    remaining = estimated_minutes * (1 - progress_percent / 100)
    urgency = remaining / max(minutes_until, 60)
    score = ((urgency * 55) + (importance / 5 * 20) + ((6 - flexibility) / 5 * 15)) * (1 + (1 - confidence_score) * .25)
    score = max(0.0, min(100.0, score))
    return score, risk_level(score), warnings


def observed_risk(commitment: dict[str, Any], *, progress_percent: int | float, skipped: bool = False) -> tuple[float, str]:
    previous_progress = float(commitment.get("progress_percent") or 0)
    score = float(commitment.get("risk_score") or 40)
    if skipped:
        score = min(100.0, score + 15)
    else:
        score = max(0.0, score - max(0.0, float(progress_percent) - previous_progress) * .5)
    return score, risk_level(score)


def parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def duration_minutes(item: dict[str, Any]) -> int:
    return max(0, int((parse_datetime(item["end_at"]) - parse_datetime(item["start_at"])).total_seconds() // 60))


def active_commitments(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("status") in ACTIVE_COMMITMENT_STATUSES and row.get("status") != "completed"]


def rank_commitments(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ceiling = datetime.max.replace(tzinfo=timezone.utc)
    return sorted(
        active_commitments(rows),
        key=lambda row: (
            -RISK_WEIGHT.get(str(row.get("risk_level")), 0),
            parse_datetime(row["deadline_at"]) if row.get("deadline_at") else ceiling,
            -int(row.get("importance") or 0),
            str(row.get("id")),
        ),
    )


def focus_view(block: dict[str, Any], *, now: datetime | None = None) -> ActiveFocusView:
    current = now or datetime.now(timezone.utc)
    start = parse_datetime(block.get("started_at") or block["start_at"])
    end = parse_datetime(block["end_at"])
    planned = max(1, int((end - parse_datetime(block["start_at"])).total_seconds() // 60))
    pause_seconds = int(block.get("accumulated_pause_seconds") or 0)
    effective_now = parse_datetime(block["paused_at"]) if block.get("status") == "paused" and block.get("paused_at") else current
    elapsed = max(0, int((effective_now - start).total_seconds()) - pause_seconds)
    return ActiveFocusView(
        id=str(block["id"]),
        commitment_id=str(block["commitment_id"]),
        title=str(block["title"]),
        status=block["status"],
        planned_minutes=planned,
        elapsed_seconds=elapsed,
        remaining_seconds=max(0, planned * 60 - elapsed),
        started_at=start,
        paused_at=parse_datetime(block["paused_at"]) if block.get("paused_at") else None,
    )


class CoreJourneyService:
    def __init__(self, repositories: RepositorySet, selector: StrategySelector | None = None):
        self.repositories = repositories
        self.selector = selector or StrategySelector()
        self.capacity_engine = CapacityEngine()

    def _profile(self, user_id: str) -> PlanningProfile:
        return PlanningProfile.model_validate(self.repositories.planning_profiles.get(user_id))

    def _calendar_context(self, user_id: str, events: list[dict[str, Any]]) -> tuple[str, str | None]:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            return "configuration_missing", None
        status = self.repositories.google_connections.get_status(user_id)
        raw_state = str(status.get("state") or "unavailable")
        last_sync = status.get("last_successful_sync")
        if raw_state == "unavailable":
            return "unavailable", last_sync
        if raw_state != "connected":
            return "disconnected", None
        if not last_sync:
            return ("cached" if events else "unavailable"), None
        try:
            age = datetime.now(timezone.utc) - parse_datetime(last_sync)
        except (TypeError, ValueError):
            return "stale", str(last_sync)
        if age <= timedelta(minutes=5):
            return "live", str(last_sync)
        if age <= timedelta(hours=24):
            return "cached", str(last_sync)
        return "stale", str(last_sync)

    @staticmethod
    def _capacity_view(result: CapacityResult) -> CapacityView:
        return CapacityView(
            total_minutes=result.total_available_minutes,
            busy_minutes=result.busy_minutes,
            planned_minutes=result.planned_minutes,
            buffer_minutes=result.buffer_minutes,
            available_minutes=result.remaining_minutes,
            total_available_minutes=result.total_available_minutes,
            scheduled_minutes=result.scheduled_minutes,
            remaining_minutes=result.remaining_minutes,
            over_capacity_minutes=result.over_capacity_minutes,
            confidence=result.confidence,
            sources=result.sources,
            calendar_state=result.calendar_state,
            last_successful_sync=result.last_successful_sync,
            retry_available=result.retry_available,
        )

    def strategy_context(self, user_id: str, ranked: list[dict[str, Any]], blocks: list[dict[str, Any]], events: list[dict[str, Any]], active: dict[str, Any] | None, capacity: CapacityResult, profile: PlanningProfile) -> StrategyContext:
        if not ranked:
            return StrategyContext()
        next_item = ranked[0]
        remaining = sum(max(0, int(row.get("estimated_minutes") or 0) - int(row.get("actual_minutes") or 0)) for row in ranked)
        free = capacity.remaining_minutes
        estimate = max(0, int(next_item.get("estimated_minutes") or 0) - int(next_item.get("actual_minutes") or 0))
        tasks = self.repositories.commitments.list_tasks_for_user(user_id)
        quick_tasks = sum(1 for task in tasks if task.get("status") not in {"completed", "archived"} and 0 < int(task.get("estimated_minutes") or 0) <= profile.quick_task_threshold_minutes)
        deadline_minutes = None
        if next_item.get("deadline_at"):
            deadline_minutes = max(0, int((parse_datetime(next_item["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() // 60))
        scheduled_ids = {str(row.get("commitment_id")) for row in blocks if row.get("commitment_id")}
        return StrategyContext(
            task_title=next_item.get("title"),
            estimate_minutes=estimate,
            similar_quick_tasks=quick_tasks,
            deep_work_active=active is not None,
            urgent=str(next_item.get("risk_level")) in {"critical", "rescue_required"},
            important=int(next_item.get("importance") or 0) >= 4,
            deadline_minutes=deadline_minutes,
            remaining_work_minutes=remaining,
            free_minutes=free,
            major_outcomes=sum(1 for row in ranked if int(row.get("importance") or 0) >= 4),
            short_tasks=quick_tasks,
            maintenance_tasks=sum(1 for row in ranked if row.get("type") in {"habit", "recurring_obligation"}),
            recurring=next_item.get("type") in {"habit", "recurring_obligation"},
            needs_scheduling=str(next_item.get("id")) not in scheduled_ids,
            energy_samples=0,
            energy_confidence=0,
        )

    def today(self, user_id: str, *, now: datetime | None = None) -> TodayResponse:
        current = now or datetime.now(timezone.utc)
        profile = self._profile(user_id)
        local_current = current.astimezone(ZoneInfo(profile.timezone))
        day_start = local_current.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        ranked = rank_commitments(self.repositories.commitments.list_for_user(user_id))
        blocks = self.repositories.focus.list_for_user(user_id, day_start, day_end)
        events = self.repositories.planning.list_calendar_events(user_id, day_start, day_end)
        pending = self.repositories.planning.list_pending(user_id)
        active = self.repositories.focus.get_active(user_id)
        calendar_state, last_sync = self._calendar_context(user_id, events)
        usable_events = [row for row in events if row.get("source") != "google"]
        if calendar_state in {"live", "cached", "stale", "unavailable"}:
            usable_events.extend(row for row in events if row.get("source") == "google")
        capacity = self.capacity_engine.calculate_day(local_current.date(), profile, calendar_events=usable_events, plan_blocks=blocks, calendar_state=calendar_state, last_successful_sync=last_sync)

        next_action = None
        if ranked:
            next_row = ranked[0]
            project = self.repositories.projects.get_for_user(user_id, str(next_row["project_id"])) if next_row.get("project_id") else None
            outcome = self.repositories.outcomes.get_for_user(user_id, str(next_row["outcome_id"])) if next_row.get("outcome_id") else None
            next_action = NextActionView(
                commitment_id=str(next_row["id"]),
                title=str(next_row["title"]),
                detail=str(next_row.get("description") or "Define the smallest visible step that moves this forward."),
                estimated_minutes=max(0, int(next_row.get("estimated_minutes") or 0) - int(next_row.get("actual_minutes") or 0)),
                project={"id": str(project["id"]), "title": project["title"]} if project else None,
                outcome={"id": str(outcome["id"]), "title": outcome["title"]} if outcome else None,
            )
        plan_limit = 3 if profile.planning_style == "minimal" else 5
        ordered = [
            PlanItemView(id=str(row["id"]), kind="commitment", title=str(row["title"]), commitment_id=str(row["id"]), status=str(row.get("risk_level") or row.get("status") or "active"))
            for row in ranked[:plan_limit]
        ]
        attention = sum(1 for row in ranked if row.get("risk_level") in {"at_risk", "critical", "rescue_required"})
        enabled = {StrategyId(value) for value in profile.strategy_preferences if value in {item.value for item in StrategyId}}
        recommendation = self.selector.recommend(
            self.strategy_context(user_id, ranked, blocks, events, active, capacity, profile),
            StrategyPreferences(enabled=enabled, quick_task_threshold_minutes=min(profile.quick_task_threshold_minutes, 15), focus_minutes=profile.default_focus_duration_minutes, quick_task_mode=profile.quick_task_mode),
        )
        high_value_only = profile.planning_style == "minimal" or profile.recommendation_frequency == "low"
        if recommendation and high_value_only and not (recommendation.confidence == "high" and (attention > 0 or capacity.over_capacity_minutes > 0)):
            recommendation = None
        elif recommendation and profile.recommendation_frequency == "normal" and recommendation.confidence == "medium" and attention == 0:
            recommendation = None
        if recommendation:
            prior = next((row for row in self.repositories.feedback.list_for_user(user_id, 30) if row.get("recommendation_type") == "strategy" and row.get("recommendation_key") == recommendation.strategy.value), None)
            if prior and prior.get("user_action") == "dismissed":
                recommendation = None
        recovery = None
        failure_mode = None
        what_changed = None
        if ranked and capacity.over_capacity_minutes > 0:
            failure_mode, what_changed = "overload", f"Today exceeds available capacity by {capacity.over_capacity_minutes} minutes."
        elif active:
            active_state = focus_view(active, now=current)
            next_event = min((parse_datetime(row["start_at"]) for row in events if parse_datetime(row["start_at"]) > current), default=None)
            if next_event and int((next_event - current).total_seconds()) < active_state.remaining_seconds + profile.minimum_transition_buffer_minutes * 60:
                failure_mode, what_changed = "calendar_disruption", "The current focus session no longer fits before the next calendar event."
        if not failure_mode and ranked and ranked[0].get("status") == "blocked":
            failure_mode, what_changed = "dependency_blocked", "The next important outcome is waiting on a dependency."
        if not failure_mode and ranked and (not ranked[0].get("description") or float(ranked[0].get("confidence_score") or 0) < .6):
            failure_mode, what_changed = "ambiguous_next_action", "The next action is not yet specific enough to execute confidently."
        if not failure_mode and any(row.get("status") in {"skipped", "scheduled"} and parse_datetime(row["end_at"]) < current for row in blocks):
            failure_mode, what_changed = "missed_focus_block", "A planned focus block passed without being completed."
        if not failure_mode and attention and ranked:
            failure_mode, what_changed = "overload", f"{ranked[0]['title']} is at risk within the current plan."
        recovery_threshold_met = bool(failure_mode and ranked)
        if profile.planning_style == "minimal" and failure_mode not in {"overload", "calendar_disruption", "dependency_blocked"}:
            recovery_threshold_met = False
        elif profile.planning_style != "guided" and failure_mode in {"ambiguous_next_action", "missed_focus_block"} and attention == 0:
            recovery_threshold_met = False
        if recovery_threshold_met and ranked:
            option_sets = {
                "calendar_disruption": (
                    {"id": "shorter_block", "title": "Use the remaining short window", "rationale": "Protect only the time that still fits.", "tradeoff": "Less progress now, without running into the meeting.", "expected_impact": "A smaller valid block", "feasible": True, "requires_approval": True},
                    {"id": "reschedule", "title": "Reschedule the remaining work", "rationale": "Move the unfinished portion to a conflict-free interval.", "tradeoff": "Another item may need to move.", "expected_impact": "Forty minutes preserved later", "feasible": True, "requires_approval": True},
                    {"id": "stop_reflect", "title": "Stop and reflect", "rationale": "Close the session honestly before the interruption.", "tradeoff": "The work remains unfinished.", "expected_impact": "Clean context for replanning", "feasible": True, "requires_approval": True},
                ),
                "dependency_blocked": (
                    {"id": "missing_information", "title": "Identify what is missing", "rationale": "Make the dependency explicit before scheduling execution.", "tradeoff": "The outcome stays paused meanwhile.", "expected_impact": "A clear unblock condition", "feasible": True, "requires_approval": True},
                    {"id": "lower_effort", "title": "Switch to executable work", "rationale": "Use available capacity without pretending blocked work can proceed.", "tradeoff": "The blocked outcome waits.", "expected_impact": "Useful progress elsewhere", "feasible": True, "requires_approval": True},
                ),
            }
            default_options = (
                {"id": "smaller_step", "title": "Define a smaller next step", "rationale": "Reduce the immediate scope to one executable result.", "tradeoff": "The full outcome moves later.", "expected_impact": "Lower start friction", "feasible": True, "requires_approval": True},
                {"id": "shorter_block", "title": "Protect a shorter block", "rationale": "Fit progress into current capacity.", "tradeoff": "Less work completes today.", "expected_impact": "A credible plan", "feasible": True, "requires_approval": True},
                {"id": "defer", "title": "Defer lower-priority work", "rationale": "Make room for the most important outcome.", "tradeoff": "Some work moves explicitly.", "expected_impact": "Reduced overload", "feasible": True, "requires_approval": True},
            )
            options = option_sets.get(failure_mode, default_options)
            recovery = RecoveryView(
                recommendation_key=f"today:{ranked[0]['id']}:{failure_mode}",
                commitment_id=str(ranked[0]["id"]),
                title="Adjust the plan calmly",
                what_changed=str(what_changed),
                failure_mode=str(failure_mode),
                reason=f"{ranked[0]['title']} needs a smaller or better-protected path.",
                options=options,
                recommended_option_id=options[0]["id"],
            )
        status = "empty" if not ranked else "attention" if attention else "clear"
        persisted_occurrences = {(str(item["routine_id"]), str(item["occurrence_date"])): item for item in self.repositories.routines.list_occurrences(user_id, day_start, day_end)}
        routines_due = []
        for routine in self.repositories.routines.list_for_user(user_id):
            if routine.get("active") and local_current.weekday() in routine.get("preferred_days", []):
                occurrence = persisted_occurrences.get((str(routine["id"]), local_current.date().isoformat()))
                if not occurrence or occurrence.get("status") == "due":
                    routines_due.append({"id": str(routine["id"]), "title": routine["title"], "preferred_time": str(routine.get("preferred_time") or "")[:5] or None, "duration_minutes": routine["estimated_duration_minutes"], "minimum_viable_version": routine["minimum_viable_version"]})
        explanation_detail = "detailed" if profile.planning_style == "guided" and profile.explanation_detail == "standard" else "brief" if profile.planning_style == "minimal" and profile.explanation_detail == "standard" else profile.explanation_detail
        return TodayResponse(
            status=status,
            status_message="Nothing needs scheduling yet." if status == "empty" else "One decision can make the plan workable." if status == "attention" else "The plan is workable.",
            next_action=next_action,
            ordered_plan=ordered,
            attention_count=attention,
            strategy_recommendation=recommendation,
            pending_approval_count=len(pending),
            active_focus_session=focus_view(active, now=current) if active else None,
            recovery=recovery,
            explanation={
                "detail": explanation_detail,
                "constraints_considered": [] if explanation_detail == "brief" else ["risk", "deadline", "importance", "calendar", "available capacity"],
                "next_action_reason": "The next action is the highest-ranked executable commitment after deterministic checks." if next_action else "No executable commitment is available.",
                "deferred": [row["title"] for row in ranked[1:(2 if explanation_detail == "standard" else 4)]] if explanation_detail != "brief" else [],
                "changed": "Loading Today did not change the plan." if explanation_detail != "brief" else "",
                "ai_used": False,
                "requires_approval": True,
            },
            routines_due=routines_due[:3],
            focus_duration_options=profile.preferred_focus_durations,
            explanation_detail=explanation_detail,
        )

    def plan(self, user_id: str, start_at: datetime, end_at: datetime) -> PlanResponse:
        profile = self._profile(user_id)
        commitments = rank_commitments(self.repositories.commitments.list_for_user(user_id))
        events = self.repositories.planning.list_calendar_events(user_id, start_at, end_at)
        blocks = self.repositories.focus.list_for_user(user_id, start_at, end_at)
        scheduled_ids = {str(block.get("commitment_id")) for block in blocks if block.get("commitment_id") and block.get("status") not in {"skipped", "moved"}}
        event_views = [PlanItemView(id=str(row["id"]), kind="calendar_event", title=str(row["title"]), start_at=parse_datetime(row["start_at"]), end_at=parse_datetime(row["end_at"]), status="busy") for row in events]
        block_views = [PlanItemView(id=str(row["id"]), kind="focus_block", title=str(row["title"]), start_at=parse_datetime(row["start_at"]), end_at=parse_datetime(row["end_at"]), commitment_id=str(row["commitment_id"]) if row.get("commitment_id") else None, status=str(row.get("status") or "scheduled")) for row in blocks]
        unscheduled = [PlanItemView(id=str(row["id"]), kind="commitment", title=str(row["title"]), commitment_id=str(row["id"]), status=str(row.get("risk_level") or "active")) for row in commitments if str(row["id"]) not in scheduled_ids]
        calendar_state, last_sync = self._calendar_context(user_id, events)
        usable_events = [row for row in events if row.get("source") != "google"]
        if calendar_state in {"live", "cached", "stale", "unavailable"}:
            usable_events.extend(row for row in events if row.get("source") == "google")
        capacity = self.capacity_engine.calculate_day(
            start_at.astimezone(ZoneInfo(profile.timezone)).date(),
            profile,
            calendar_events=usable_events,
            plan_blocks=blocks,
            calendar_state=calendar_state,
            last_successful_sync=last_sync,
        )
        timeline = sorted([*event_views, *block_views], key=lambda row: row.start_at or end_at)
        return PlanResponse(
            timezone=profile.timezone,
            range_start=start_at,
            range_end=end_at,
            calendar_events=event_views,
            plan_blocks=block_views,
            unscheduled_commitments=unscheduled,
            ordered_timeline=timeline,
            capacity=self._capacity_view(capacity),
            buffer_guidance=f"Keep at least {profile.minimum_transition_buffer_minutes} minutes between blocks and {profile.minimum_daily_unscheduled_buffer_minutes} minutes unscheduled each day.",
            explanation={
                "constraints_considered": ["personal availability", "calendar", "transition buffer", "daily focus limit"],
                "next_action_reason": "Commitments are ordered by risk, deadline, importance, and stable identifier.",
                "deferred": [item.title for item in unscheduled[1:4]],
                "changed": "No plan changes were made while loading this view.",
                "ai_used": False,
                "requires_approval": True,
            },
        )

    def create_plan_block(self, user_id: str, commitment_id: str, start_at: datetime, duration: int, title: str | None, block_type: str) -> dict[str, Any]:
        commitment = self.repositories.commitments.get_for_user(user_id, commitment_id)
        if not commitment:
            raise ChronosError(ErrorCode.VALIDATION, "Commitment not found.")
        end_at = start_at + timedelta(minutes=duration)
        profile = self._profile(user_id)
        local_start = start_at.astimezone(ZoneInfo(profile.timezone))
        local_end = end_at.astimezone(ZoneInfo(profile.timezone))
        if local_start.date() != local_end.date() or local_start.weekday() not in profile.available_weekdays:
            raise ChronosError(ErrorCode.CONFLICT, "That time is outside your available planning days.")
        if local_start.time() < profile.working_start_time or local_end.time() > profile.working_end_time:
            raise ChronosError(ErrorCode.CONFLICT, "That block is outside your working hours.")
        if profile.protected_interval_start and profile.protected_interval_end and local_start.time() < profile.protected_interval_end and local_end.time() > profile.protected_interval_start:
            raise ChronosError(ErrorCode.CONFLICT, "That block overlaps your protected interval.")
        events = self.repositories.planning.list_calendar_events(user_id, start_at, end_at)
        blocks = self.repositories.focus.list_for_user(user_id, start_at, end_at)
        conflicts = [row for row in [*events, *blocks] if parse_datetime(row["start_at"]) < end_at and parse_datetime(row["end_at"]) > start_at and row.get("status") not in {"skipped", "moved"}]
        if conflicts:
            raise ChronosError(ErrorCode.CONFLICT, f"That time overlaps with {conflicts[0].get('title', 'an existing item')}.")
        buffer = timedelta(minutes=profile.minimum_transition_buffer_minutes)
        nearby_events = self.repositories.planning.list_calendar_events(user_id, start_at - buffer, end_at + buffer)
        nearby_blocks = self.repositories.focus.list_for_user(user_id, start_at - buffer, end_at + buffer)
        too_close = [row for row in [*nearby_events, *nearby_blocks] if row.get("status") not in {"skipped", "moved"} and parse_datetime(row["start_at"]) < end_at + buffer and parse_datetime(row["end_at"]) > start_at - buffer]
        if too_close:
            raise ChronosError(ErrorCode.CONFLICT, f"Leave a {profile.minimum_transition_buffer_minutes}-minute transition around {too_close[0].get('title', 'the existing item')}.")
        day_start = start_at.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_plan = self.plan(user_id, day_start, day_end)
        if duration > day_plan.capacity.available_minutes:
            raise ChronosError(ErrorCode.CONFLICT, "That block does not fit the available capacity for this day.")
        return self.repositories.focus.create(user_id, {
            "id": str(uuid.uuid4()),
            "commitment_id": commitment_id,
            "title": title or str(commitment["title"]),
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "block_type": block_type,
            "status": "scheduled",
        })
