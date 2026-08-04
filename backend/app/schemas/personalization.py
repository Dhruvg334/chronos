from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.planning_profile import PlanningProfile


class OnboardingSaveRequest(PlanningProfile):
    complete: bool = False


class PreferenceUpdate(BaseModel):
    planning_style: Literal["guided", "balanced", "minimal"]
    recommendation_frequency: Literal["low", "normal", "high"]
    approval_strictness: Literal["always_ask", "allow_reversible"]
    internal_write_automation_enabled: bool = False
    preferred_focus_durations: list[int] = Field(min_length=1, max_length=5)
    routine_continuity_preference: Literal["gentle", "standard", "structured"]
    quick_task_mode: Literal["immediate", "batch"]
    strategy_preferences: list[str] = Field(min_length=1, max_length=10)
    explanation_detail: Literal["brief", "standard", "detailed"]

    @model_validator(mode="after")
    def validate_preferences(self):
        supported_durations = {15, 20, 25, 30, 45, 60, 90, 120, 180}
        if len(set(self.preferred_focus_durations)) != len(self.preferred_focus_durations) or any(value not in supported_durations for value in self.preferred_focus_durations):
            raise ValueError("Choose unique supported focus durations.")
        supported_strategies = {"eisenhower_triage", "task_batching", "continuity_recovery", "focus_interval", "constrained_day", "quick_action", "time_blocking"}
        if any(value not in supported_strategies for value in self.strategy_preferences):
            raise ValueError("One or more strategy preferences are unsupported.")
        if self.internal_write_automation_enabled and self.approval_strictness != "allow_reversible":
            raise ValueError("Internal-write automation requires reversible internal changes to be allowed.")
        return self


class RecommendationFeedbackCreate(BaseModel):
    recommendation_type: str = Field(min_length=1, max_length=80)
    recommendation_key: str | None = Field(default=None, max_length=160)
    context_summary: dict[str, Any] = Field(default_factory=dict)
    user_action: Literal["useful", "not_useful", "used", "dismissed", "edited_before_use", "postponed"]
    reason_category: Literal["not_relevant", "bad_timing", "too_much_effort", "already_handled", "other"] | None = None


class RecoveryChoiceCreate(BaseModel):
    recommendation_key: str = Field(min_length=1, max_length=160)
    choice: Literal["used", "dismissed", "postponed", "edited_before_use"]
    failure_mode: str = Field(min_length=1, max_length=80)
    option_id: str | None = Field(default=None, max_length=80)
    reason_category: Literal["not_relevant", "bad_timing", "too_much_effort", "already_handled", "other"] | None = None
