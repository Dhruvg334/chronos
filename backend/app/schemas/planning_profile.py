from __future__ import annotations

from datetime import time
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator, model_validator


class PlanningProfile(BaseModel):
    timezone: str = "UTC"
    available_weekdays: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6], min_length=1, max_length=7)
    working_start_time: time = time(9, 0)
    working_end_time: time = time(17, 0)
    daily_focus_limit_minutes: int = Field(default=240, ge=15, le=1440)
    default_focus_duration_minutes: int = Field(default=45, ge=5, le=180)
    minimum_transition_buffer_minutes: int = Field(default=10, ge=0, le=120)
    minimum_daily_unscheduled_buffer_minutes: int = Field(default=60, ge=0, le=720)
    protected_interval_start: time | None = None
    protected_interval_end: time | None = None
    quick_task_threshold_minutes: int = Field(default=5, ge=1, le=60)
    onboarding_status: Literal["not_started", "in_progress", "completed", "skipped"] = "not_started"
    onboarding_step: int = Field(default=1, ge=1, le=3)
    onboarding_completed_at: str | None = None
    planning_style: Literal["guided", "balanced", "minimal"] = "balanced"
    recommendation_frequency: Literal["low", "normal", "high"] = "normal"
    approval_strictness: Literal["always_ask", "allow_reversible"] = "always_ask"
    internal_write_automation_enabled: bool = False
    preferred_focus_durations: list[int] = Field(default_factory=lambda: [25, 45, 60], min_length=1, max_length=5)
    routine_continuity_preference: Literal["gentle", "standard", "structured"] = "gentle"
    quick_task_mode: Literal["immediate", "batch"] = "batch"
    strategy_preferences: list[str] = Field(default_factory=lambda: ["eisenhower_triage", "task_batching", "continuity_recovery", "focus_interval", "constrained_day", "quick_action", "time_blocking"])
    explanation_detail: Literal["brief", "standard", "detailed"] = "standard"

    @field_validator("timezone")
    @classmethod
    def timezone_exists(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Use a valid IANA timezone, such as Asia/Kolkata.") from exc
        return value

    @field_validator("available_weekdays")
    @classmethod
    def valid_weekdays(cls, value: list[int]) -> list[int]:
        if any(day < 0 or day > 6 for day in value):
            raise ValueError("Weekdays must be between Monday (0) and Sunday (6).")
        if len(set(value)) != len(value):
            raise ValueError("Available weekdays cannot contain duplicates.")
        return sorted(value)

    @model_validator(mode="after")
    def valid_windows(self):
        if self.working_end_time <= self.working_start_time:
            raise ValueError("Working end time must be after the start time.")
        paired = self.protected_interval_start is not None and self.protected_interval_end is not None
        if (self.protected_interval_start is None) != (self.protected_interval_end is None):
            raise ValueError("Both protected interval times are required.")
        if paired:
            assert self.protected_interval_start is not None and self.protected_interval_end is not None
            if not self.working_start_time <= self.protected_interval_start < self.protected_interval_end <= self.working_end_time:
                raise ValueError("The protected interval must fit inside working hours.")
        allowed_durations = {15, 20, 25, 30, 45, 60, 90, 120, 180}
        if len(set(self.preferred_focus_durations)) != len(self.preferred_focus_durations) or any(value not in allowed_durations for value in self.preferred_focus_durations):
            raise ValueError("Preferred focus durations must be unique supported minute values.")
        if self.internal_write_automation_enabled and self.approval_strictness != "allow_reversible":
            raise ValueError("Enable reversible internal changes before enabling internal-write automation.")
        return self


class PlanningProfileResponse(PlanningProfile):
    updated_at: str | None = None


class IntegrationStatus(BaseModel):
    provider: str = "google_calendar"
    access: str = "read_only"
    state: str
    last_successful_sync: str | None = None
    retry_available: bool
    planning_mode: str
    message: str
