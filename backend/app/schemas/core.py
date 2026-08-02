from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.strategies.models import StrategyContext, StrategyRecommendation


class NextActionView(BaseModel):
    commitment_id: str
    task_id: str | None = None
    title: str
    detail: str
    estimated_minutes: int


class PlanItemView(BaseModel):
    id: str
    kind: Literal["calendar_event", "focus_block", "commitment"]
    title: str
    start_at: datetime | None = None
    end_at: datetime | None = None
    commitment_id: str | None = None
    status: str


class ActiveFocusView(BaseModel):
    id: str
    commitment_id: str
    title: str
    status: Literal["active", "paused"]
    planned_minutes: int
    elapsed_seconds: int
    remaining_seconds: int
    started_at: datetime
    paused_at: datetime | None = None


class RecoveryView(BaseModel):
    commitment_id: str
    title: str
    reason: str
    options: tuple[str, ...]
    requires_approval: Literal[True] = True


class TodayResponse(BaseModel):
    status: Literal["clear", "attention", "empty"]
    status_message: str
    next_action: NextActionView | None
    ordered_plan: list[PlanItemView]
    attention_count: int
    strategy_recommendation: StrategyRecommendation | None = None
    pending_approval_count: int
    active_focus_session: ActiveFocusView | None = None
    recovery: RecoveryView | None = None


class StrategyRecommendationRequest(BaseModel):
    context: StrategyContext | None = None


class StrategyRecommendationResponse(BaseModel):
    recommendation: StrategyRecommendation | None


class CapacityView(BaseModel):
    total_minutes: int
    busy_minutes: int
    planned_minutes: int
    buffer_minutes: int
    available_minutes: int


class PlanResponse(BaseModel):
    range_start: datetime
    range_end: datetime
    calendar_events: list[PlanItemView]
    plan_blocks: list[PlanItemView]
    unscheduled_commitments: list[PlanItemView]
    ordered_timeline: list[PlanItemView]
    capacity: CapacityView
    buffer_guidance: str


class CreatePlanBlockRequest(BaseModel):
    commitment_id: str
    start_at: datetime
    duration_minutes: int = Field(ge=10, le=480)
    title: str | None = Field(default=None, max_length=180)
    block_type: Literal["deep_work", "shallow_work", "admin", "buffer"] = "deep_work"


class StartFocusRequest(BaseModel):
    commitment_id: str
    duration_minutes: int = Field(default=25, ge=5, le=180)
    title: str | None = Field(default=None, max_length=180)


class CompleteFocusRequest(BaseModel):
    actual_minutes: int = Field(ge=0, le=720)
    completion_status: Literal["completed", "partial"]
    energy_level: int = Field(ge=1, le=5)
    progress_percent: int = Field(ge=0, le=100)
    blocker_reason: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)


class StopFocusRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


class StuckResponse(BaseModel):
    focus_block_id: str
    options: tuple[str, ...]
    recovery_available: bool


class RecoveryProposalRequest(BaseModel):
    commitment_id: str
    action: Literal["smaller_next_step", "protect_short_block", "defer_lower_priority"]


class ApproveRecoveryRequest(BaseModel):
    approved: bool


class ReflectionRequest(BaseModel):
    commitment_id: str
    focus_block_id: str | None = None
    planned_minutes: int = Field(ge=0)
    actual_minutes: int = Field(ge=0)
    completion_status: Literal["completed", "partial", "skipped"]
    energy_level: int = Field(ge=1, le=5)
    progress_percent: int | None = Field(default=None, ge=0, le=100)
    blocker_reason: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)


class FocusSessionResponse(BaseModel):
    session: ActiveFocusView | None
    reflection: dict | None = None
    reflection_requested: bool = False


class DateRangeQuery(BaseModel):
    start_at: datetime
    end_at: datetime

    @model_validator(mode="after")
    def valid_range(self):
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self
