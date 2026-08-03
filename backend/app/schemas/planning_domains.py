from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field, model_validator

ProjectStatus = Literal["active", "paused", "completed", "archived"]
OutcomeStatus = Literal["active", "blocked", "uncertain", "completed", "archived"]
RoutineOccurrenceStatus = Literal["due", "completed", "minimum_completed", "skipped"]


def _validate_weekdays(days: list[int]) -> None:
    if any(day < 0 or day > 6 for day in days) or len(set(days)) != len(days):
        raise ValueError("preferred days must be unique weekday numbers from 0 to 6")


class ProjectWrite(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    description: str = Field(default="", max_length=2000)
    status: ProjectStatus = "active"
    target_date: date | None = None
    colour: str = Field(default="accent", min_length=1, max_length=32)


class ProjectPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=2000)
    status: ProjectStatus | None = None
    target_date: date | None = None
    colour: str | None = Field(default=None, min_length=1, max_length=32)


class OutcomeWrite(BaseModel):
    project_id: str | None = None
    title: str = Field(min_length=1, max_length=180)
    description: str = Field(default="", max_length=2000)
    status: OutcomeStatus = "active"
    target_date: date | None = None
    importance: int = Field(default=3, ge=1, le=5)
    estimated_effort_minutes: int | None = Field(default=None, ge=5, le=100000)
    confidence: float = Field(default=0.5, ge=0, le=1)
    completion_criteria: str = Field(min_length=1, max_length=1000)
    provenance: str | None = Field(default=None, max_length=500)


class OutcomePatch(BaseModel):
    project_id: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=2000)
    status: OutcomeStatus | None = None
    target_date: date | None = None
    importance: int | None = Field(default=None, ge=1, le=5)
    estimated_effort_minutes: int | None = Field(default=None, ge=5, le=100000)
    confidence: float | None = Field(default=None, ge=0, le=1)
    completion_criteria: str | None = Field(default=None, min_length=1, max_length=1000)


class LinkWorkRequest(BaseModel):
    commitment_ids: list[str] = Field(default_factory=list, max_length=50)
    task_ids: list[str] = Field(default_factory=list, max_length=100)


class RoutineWrite(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    frequency_rule: Literal["daily", "weekly"] = "weekly"
    preferred_days: list[int] = Field(min_length=1, max_length=7)
    preferred_time: time | None = None
    minimum_viable_version: str = Field(min_length=1, max_length=500)
    estimated_duration_minutes: int = Field(ge=5, le=480)
    active: bool = True

    @model_validator(mode="after")
    def validate_days(self):
        _validate_weekdays(self.preferred_days)
        return self


class RoutinePatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=180)
    frequency_rule: Literal["daily", "weekly"] | None = None
    preferred_days: list[int] | None = Field(default=None, min_length=1, max_length=7)
    preferred_time: time | None = None
    minimum_viable_version: str | None = Field(default=None, min_length=1, max_length=500)
    estimated_duration_minutes: int | None = Field(default=None, ge=5, le=480)
    active: bool | None = None

    @model_validator(mode="after")
    def validate_days(self):
        if self.preferred_days is not None:
            _validate_weekdays(self.preferred_days)
        return self


class RoutineOccurrenceUpdate(BaseModel):
    occurrence_date: date
    status: RoutineOccurrenceStatus
    note: str | None = Field(default=None, max_length=500)


class WeeklyBlock(BaseModel):
    commitment_id: str
    title: str
    start_at: datetime
    duration_minutes: int = Field(ge=10, le=180)
    outcome_id: str | None = None
    project_id: str | None = None


class WeeklyProposalEdit(BaseModel):
    blocks: list[WeeklyBlock] = Field(min_length=1, max_length=12)


class WeeklyProposalAction(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)


class WeeklyDayCapacity(BaseModel):
    date: date
    available_minutes: int
    scheduled_minutes: int
    remaining_minutes: int
    buffer_minutes: int
    over_capacity_minutes: int
    confidence: Literal["low", "medium", "high"]
    sources: list[str]


class WeeklyView(BaseModel):
    week_start: date
    timezone: str
    days: list[WeeklyDayCapacity]
    due_outcomes: list[dict]
    unscheduled_work: list[dict]
    routine_occurrences: list[dict]
    active_projects: list[dict]
    primary_strategy: dict | None = None


class WeeklyProposalResponse(BaseModel):
    id: str
    status: Literal["pending", "approved", "rejected"]
    week_start: date
    focus_set: list[dict]
    blocks: list[WeeklyBlock]
    deferred: list[dict]
    explanation: dict
    requires_approval: bool = True
