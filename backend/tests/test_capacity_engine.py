from datetime import date, datetime, timezone

from app.schemas.planning_profile import PlanningProfile
from app.services.capacity_engine import CapacityEngine

DAY = date(2026, 8, 3)  # Monday


def profile(**changes):
    return PlanningProfile.model_validate({
        "timezone": "UTC", "available_weekdays": [0, 1, 2, 3, 4, 5, 6],
        "working_start_time": "09:00", "working_end_time": "17:00",
        "daily_focus_limit_minutes": 240, "default_focus_duration_minutes": 45,
        "minimum_transition_buffer_minutes": 10,
        "minimum_daily_unscheduled_buffer_minutes": 60,
        "quick_task_threshold_minutes": 5, **changes,
    })


def row(start: str, end: str, **extra):
    return {"start_at": f"2026-08-03T{start}:00+00:00", "end_at": f"2026-08-03T{end}:00+00:00", **extra}


def calculate(p=None, events=None, blocks=None, state="connected"):
    return CapacityEngine().calculate_day(DAY, p or profile(), calendar_events=events or [], plan_blocks=blocks or [], calendar_state=state)


def test_new_user_defaults_are_profile_driven():
    result = calculate()
    assert result.total_available_minutes == 240
    assert result.remaining_minutes == 240


def test_part_time_schedule():
    result = calculate(profile(working_end_time="13:00", daily_focus_limit_minutes=600))
    assert result.total_available_minutes == 180


def test_unavailable_weekend():
    result = CapacityEngine().calculate_day(date(2026, 8, 8), profile(available_weekdays=[0]), calendar_events=[], plan_blocks=[])
    assert result.total_available_minutes == 0


def test_lunch_interval_is_removed():
    result = calculate(profile(daily_focus_limit_minutes=600, protected_interval_start="13:00", protected_interval_end="14:00"))
    assert result.total_available_minutes == 360


def test_overlapping_calendar_events_are_not_double_counted():
    result = calculate(profile(daily_focus_limit_minutes=600), [row("10:00", "11:00"), row("10:30", "11:30")])
    assert result.busy_minutes == 90
    assert result.total_available_minutes == 320


def test_transition_buffers_reduce_capacity():
    result = calculate(profile(daily_focus_limit_minutes=600), [row("10:00", "11:00"), row("14:00", "15:00")])
    assert result.buffer_minutes == 80
    assert result.total_available_minutes == 280


def test_over_capacity_day_reports_excess():
    result = calculate(blocks=[row("09:00", "14:00", status="scheduled")])
    assert result.over_capacity_minutes == 60
    assert result.remaining_minutes == 0


def test_timezone_boundary_uses_profile_local_day():
    event = {"start_at": "2026-08-03T04:30:00+00:00", "end_at": "2026-08-03T05:30:00+00:00"}
    result = calculate(profile(timezone="Asia/Kolkata"), [event])
    assert result.busy_minutes == 60


def test_no_calendar_connection_is_explicit_profile_only():
    result = calculate(state="disconnected")
    assert result.confidence == "medium"
    assert "calendar_disconnected_profile_only" in result.sources


def test_calendar_unavailable_degrades_with_low_confidence():
    result = calculate(state="unavailable")
    assert result.confidence == "low"
    assert result.calendar_state == "unavailable"


def test_deadline_window_clips_first_and_last_day():
    result = CapacityEngine().calculate_until(
        datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc),
        datetime(2026, 8, 3, 15, 0, tzinfo=timezone.utc),
        profile(daily_focus_limit_minutes=600, minimum_daily_unscheduled_buffer_minutes=0),
        calendar_events=[], plan_blocks=[], calendar_state="disconnected",
    )
    assert result.total_available_minutes == 180
