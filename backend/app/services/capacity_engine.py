from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from app.schemas.planning_profile import PlanningProfile

Interval = tuple[datetime, datetime]


@dataclass(frozen=True)
class CapacityResult:
    total_available_minutes: int
    scheduled_minutes: int
    remaining_minutes: int
    buffer_minutes: int
    over_capacity_minutes: int
    busy_minutes: int
    planned_minutes: int
    confidence: str
    sources: tuple[str, ...]
    calendar_state: str
    last_successful_sync: str | None = None
    retry_available: bool = False

    def model_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _merge(intervals: Iterable[Interval]) -> list[Interval]:
    ordered = sorted((start, end) for start, end in intervals if end > start)
    merged: list[list[datetime]] = []
    for start, end in ordered:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def _minutes(intervals: Iterable[Interval]) -> int:
    return sum(max(0, int((end - start).total_seconds() // 60)) for start, end in _merge(intervals))


def _clip(rows: Iterable[dict[str, Any]], start: datetime, end: datetime) -> list[Interval]:
    result: list[Interval] = []
    for row in rows:
        row_start = _as_datetime(row["start_at"]).astimezone(start.tzinfo)
        row_end = _as_datetime(row["end_at"]).astimezone(start.tzinfo)
        clipped = (max(start, row_start), min(end, row_end))
        if clipped[1] > clipped[0]:
            result.append(clipped)
    return result


class CapacityEngine:
    """Deterministic availability math. The profile is the only work-hours authority."""

    def calculate_day(
        self,
        day: date,
        profile: PlanningProfile,
        *,
        calendar_events: list[dict[str, Any]],
        plan_blocks: list[dict[str, Any]],
        calendar_state: str = "disconnected",
        last_successful_sync: str | None = None,
        window_start: datetime | None = None,
        window_end: datetime | None = None,
    ) -> CapacityResult:
        sources = ["personal_availability"]
        confidence = "high"
        if calendar_state in {"connected", "live"}:
            sources.append("live_calendar")
        elif calendar_state == "cached":
            sources.append("cached_calendar")
            confidence = "medium"
        elif calendar_state == "stale":
            sources.append("stale_calendar")
            confidence = "low"
        elif calendar_state == "unavailable" and calendar_events:
            sources.append("cached_calendar_provider_unavailable")
            confidence = "low"
        elif calendar_state == "unavailable":
            sources.append("calendar_unavailable_profile_only")
            confidence = "low"
        elif calendar_state == "configuration_missing":
            sources.append("calendar_configuration_missing_profile_only")
            confidence = "medium"
        else:
            sources.append("calendar_disconnected_profile_only")
            confidence = "medium"

        if day.weekday() not in profile.available_weekdays:
            return CapacityResult(0, 0, 0, 0, 0, 0, 0, confidence, tuple(sources), calendar_state, last_successful_sync, calendar_state in {"stale", "unavailable"})

        zone = ZoneInfo(profile.timezone)
        work_start = datetime.combine(day, profile.working_start_time, zone)
        work_end = datetime.combine(day, profile.working_end_time, zone)
        if window_start is not None:
            work_start = max(work_start, window_start.astimezone(zone))
        if window_end is not None:
            work_end = min(work_end, window_end.astimezone(zone))
        if work_end <= work_start:
            return CapacityResult(0, 0, 0, 0, 0, 0, 0, confidence, tuple(sources), calendar_state, last_successful_sync, calendar_state in {"stale", "unavailable"})
        work_minutes = int((work_end - work_start).total_seconds() // 60)

        protected: list[Interval] = []
        if profile.protected_interval_start and profile.protected_interval_end:
            protected_start = max(work_start, datetime.combine(day, profile.protected_interval_start, zone))
            protected_end = min(work_end, datetime.combine(day, profile.protected_interval_end, zone))
            if protected_end > protected_start:
                protected.append((protected_start, protected_end))

        active_blocks = [row for row in plan_blocks if row.get("status") not in {"skipped", "moved"}]
        calendar_intervals = _clip(calendar_events, work_start, work_end)
        plan_intervals = _clip(active_blocks, work_start, work_end)
        protected_minutes = _minutes(protected)
        busy_minutes = _minutes(calendar_intervals)
        planned_minutes = _minutes(plan_intervals)

        transition = timedelta(minutes=profile.minimum_transition_buffer_minutes)
        all_scheduled = _merge([*calendar_intervals, *plan_intervals])
        buffered = _merge((start, min(work_end, end + transition)) for start, end in all_scheduled)
        transition_minutes = max(0, _minutes(buffered) - _minutes(all_scheduled))
        buffer_minutes = profile.minimum_daily_unscheduled_buffer_minutes + transition_minutes

        occupied_without_plan = _minutes([*protected, *calendar_intervals])
        focus_envelope = max(0, work_minutes - occupied_without_plan - buffer_minutes)
        total_available = min(profile.daily_focus_limit_minutes, focus_envelope)
        scheduled_focus = _minutes(plan_intervals)
        remaining = max(0, total_available - scheduled_focus)
        over_capacity = max(0, scheduled_focus - total_available)
        return CapacityResult(
            total_available,
            scheduled_focus,
            remaining,
            buffer_minutes,
            over_capacity,
            busy_minutes,
            planned_minutes,
            confidence,
            tuple(sources),
            calendar_state,
            last_successful_sync,
            calendar_state in {"stale", "unavailable"},
        )

    def calculate_until(
        self,
        start: datetime,
        deadline: datetime,
        profile: PlanningProfile,
        *,
        calendar_events: list[dict[str, Any]],
        plan_blocks: list[dict[str, Any]],
        calendar_state: str = "disconnected",
        last_successful_sync: str | None = None,
    ) -> CapacityResult:
        zone = ZoneInfo(profile.timezone)
        cursor = start.astimezone(zone).date()
        final_day = deadline.astimezone(zone).date()
        results: list[CapacityResult] = []
        while cursor <= final_day:
            results.append(self.calculate_day(
                cursor, profile, calendar_events=calendar_events, plan_blocks=plan_blocks,
                calendar_state=calendar_state, last_successful_sync=last_successful_sync,
                window_start=start if cursor == start.astimezone(zone).date() else None,
                window_end=deadline if cursor == final_day else None,
            ))
            cursor += timedelta(days=1)
        if not results:
            return self.calculate_day(start.astimezone(zone).date(), profile, calendar_events=[], plan_blocks=[], calendar_state=calendar_state, last_successful_sync=last_successful_sync)
        return CapacityResult(
            sum(item.total_available_minutes for item in results),
            sum(item.scheduled_minutes for item in results),
            sum(item.remaining_minutes for item in results),
            sum(item.buffer_minutes for item in results),
            sum(item.over_capacity_minutes for item in results),
            sum(item.busy_minutes for item in results),
            sum(item.planned_minutes for item in results),
            min((item.confidence for item in results), key={"low": 0, "medium": 1, "high": 2}.get),
            results[0].sources,
            calendar_state,
            last_successful_sync,
            calendar_state in {"stale", "unavailable"},
        )
