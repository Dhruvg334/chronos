from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class StrategyId(StrEnum):
    EISENHOWER = "eisenhower_triage"
    BATCHING = "task_batching"
    CONTINUITY = "continuity_recovery"
    FOCUS_INTERVAL = "focus_interval"
    CONSTRAINED_DAY = "constrained_day"
    QUICK_ACTION = "quick_action"
    ENERGY_AWARE = "energy_aware"
    DIGITAL_RESET = "digital_reset"
    TIME_BLOCKING = "time_blocking"
    REFLECTION_LENS = "reflection_lens"


class StrategyDefinition(BaseModel):
    id: StrategyId
    name: str
    eligibility: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    contraindications: tuple[str, ...]
    explanation_template: str


class StrategyPreferences(BaseModel):
    enabled: set[StrategyId] = Field(default_factory=lambda: set(StrategyId))
    quick_task_threshold_minutes: int = Field(2, ge=1, le=15)
    focus_minutes: int = Field(45, ge=10, le=180)
    break_minutes: int = Field(10, ge=1, le=60)


class StrategyContext(BaseModel):
    weekly_planning: bool = False
    task_title: str | None = None
    estimate_minutes: int | None = None
    similar_quick_tasks: int = 0
    deep_work_active: bool = False
    urgent: bool = False
    important: bool = False
    deadline_minutes: int | None = None
    remaining_work_minutes: int | None = None
    free_minutes: int | None = None
    major_outcomes: int = 0
    short_tasks: int = 0
    maintenance_tasks: int = 0
    recurring: bool = False
    recent_completions: int = 0
    missed_yesterday: bool = False
    needs_scheduling: bool = False
    energy_samples: int = 0
    energy_confidence: float = 0.0


class StrategyRecommendation(BaseModel):
    strategy: StrategyId
    title: str
    why: str
    evidence: tuple[str, ...]
    action: str
    tradeoff: str
    automatic_change: Literal[False] = False
    confidence: Literal["low", "medium", "high"]
    alternatives: tuple[StrategyId, ...] = ()
