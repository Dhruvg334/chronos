from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.errors import ChronosError, ErrorCode
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
from app.strategies.models import StrategyContext
from app.strategies.selector import StrategySelector

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

    def strategy_context(self, user_id: str, ranked: list[dict[str, Any]], blocks: list[dict[str, Any]], events: list[dict[str, Any]], active: dict[str, Any] | None) -> StrategyContext:
        if not ranked:
            return StrategyContext()
        next_item = ranked[0]
        remaining = sum(max(0, int(row.get("estimated_minutes") or 0) - int(row.get("actual_minutes") or 0)) for row in ranked)
        busy = sum(duration_minutes(row) for row in [*blocks, *events])
        free = max(0, 8 * 60 - busy)
        estimate = max(0, int(next_item.get("estimated_minutes") or 0) - int(next_item.get("actual_minutes") or 0))
        tasks = self.repositories.commitments.list_tasks_for_user(user_id)
        quick_tasks = sum(1 for task in tasks if task.get("status") not in {"completed", "archived"} and 0 < int(task.get("estimated_minutes") or 0) <= 10)
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
        day_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        ranked = rank_commitments(self.repositories.commitments.list_for_user(user_id))
        blocks = self.repositories.focus.list_for_user(user_id, day_start, day_end)
        events = self.repositories.planning.list_calendar_events(user_id, day_start, day_end)
        pending = self.repositories.planning.list_pending(user_id)
        active = self.repositories.focus.get_active(user_id)

        next_action = None
        if ranked:
            next_row = ranked[0]
            next_action = NextActionView(
                commitment_id=str(next_row["id"]),
                title=str(next_row["title"]),
                detail=str(next_row.get("description") or "Define the smallest visible step that moves this forward."),
                estimated_minutes=max(0, int(next_row.get("estimated_minutes") or 0) - int(next_row.get("actual_minutes") or 0)),
            )
        ordered = [
            PlanItemView(id=str(row["id"]), kind="commitment", title=str(row["title"]), commitment_id=str(row["id"]), status=str(row.get("risk_level") or row.get("status") or "active"))
            for row in ranked[:6]
        ]
        attention = sum(1 for row in ranked if row.get("risk_level") in {"at_risk", "critical", "rescue_required"})
        recommendation = self.selector.recommend(self.strategy_context(user_id, ranked, blocks, events, active))
        recovery = None
        if attention and ranked:
            recovery = RecoveryView(
                commitment_id=str(ranked[0]["id"]),
                title="Make the plan credible again",
                reason=f"{ranked[0]['title']} needs a smaller or better-protected path.",
                options=("Define a smaller next step", "Protect a short focus block", "Defer lower-priority work"),
            )
        status = "empty" if not ranked else "attention" if attention else "clear"
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
        )

    def plan(self, user_id: str, start_at: datetime, end_at: datetime) -> PlanResponse:
        commitments = rank_commitments(self.repositories.commitments.list_for_user(user_id))
        events = self.repositories.planning.list_calendar_events(user_id, start_at, end_at)
        blocks = self.repositories.focus.list_for_user(user_id, start_at, end_at)
        scheduled_ids = {str(block.get("commitment_id")) for block in blocks if block.get("commitment_id") and block.get("status") not in {"skipped", "moved"}}
        event_views = [PlanItemView(id=str(row["id"]), kind="calendar_event", title=str(row["title"]), start_at=parse_datetime(row["start_at"]), end_at=parse_datetime(row["end_at"]), status="busy") for row in events]
        block_views = [PlanItemView(id=str(row["id"]), kind="focus_block", title=str(row["title"]), start_at=parse_datetime(row["start_at"]), end_at=parse_datetime(row["end_at"]), commitment_id=str(row["commitment_id"]) if row.get("commitment_id") else None, status=str(row.get("status") or "scheduled")) for row in blocks]
        unscheduled = [PlanItemView(id=str(row["id"]), kind="commitment", title=str(row["title"]), commitment_id=str(row["id"]), status=str(row.get("risk_level") or "active")) for row in commitments if str(row["id"]) not in scheduled_ids]
        # Until working-hour preferences are persisted, use a conservative eight-hour
        # daily planning envelope instead of treating all 24 hours as available work.
        total = min(8 * 60, max(0, int((end_at - start_at).total_seconds() // 60)))
        busy = sum(duration_minutes(row) for row in events)
        planned = sum(duration_minutes(row) for row in blocks if row.get("status") not in {"skipped", "moved"})
        transitions = max(0, len(events) + len(blocks) - 1)
        buffer = min(60, transitions * 10)
        available = max(0, total - busy - planned - buffer)
        timeline = sorted([*event_views, *block_views], key=lambda row: row.start_at or end_at)
        return PlanResponse(
            range_start=start_at,
            range_end=end_at,
            calendar_events=event_views,
            plan_blocks=block_views,
            unscheduled_commitments=unscheduled,
            ordered_timeline=timeline,
            capacity=CapacityView(total_minutes=total, busy_minutes=busy, planned_minutes=planned, buffer_minutes=buffer, available_minutes=available),
            buffer_guidance="Keep at least 10 minutes between demanding blocks." if transitions else "Keep some open time for transitions and unexpected work.",
        )

    def create_plan_block(self, user_id: str, commitment_id: str, start_at: datetime, duration: int, title: str | None, block_type: str) -> dict[str, Any]:
        commitment = self.repositories.commitments.get_for_user(user_id, commitment_id)
        if not commitment:
            raise ChronosError(ErrorCode.VALIDATION, "Commitment not found.")
        end_at = start_at + timedelta(minutes=duration)
        events = self.repositories.planning.list_calendar_events(user_id, start_at, end_at)
        blocks = self.repositories.focus.list_for_user(user_id, start_at, end_at)
        conflicts = [row for row in [*events, *blocks] if parse_datetime(row["start_at"]) < end_at and parse_datetime(row["end_at"]) > start_at and row.get("status") not in {"skipped", "moved"}]
        if conflicts:
            raise ChronosError(ErrorCode.CONFLICT, f"That time overlaps with {conflicts[0].get('title', 'an existing item')}.")
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
