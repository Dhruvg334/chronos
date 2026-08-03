from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CandidatePlanBlock(BaseModel):
    commitment_id: str
    start_at: datetime
    duration_minutes: int = Field(ge=10, le=180)
    rationale: str = Field(min_length=3, max_length=280)


class CandidatePlan(BaseModel):
    label: str = Field(min_length=2, max_length=80)
    summary: str = Field(min_length=3, max_length=400)
    blocks: list[CandidatePlanBlock] = Field(min_length=1, max_length=3)
    deferred_commitment_ids: list[str] = Field(default_factory=list, max_length=8)


class PlanningModelOutput(BaseModel):
    diagnosis: str = Field(min_length=3, max_length=500)
    candidates: list[CandidatePlan] = Field(min_length=1, max_length=3)


class PlanExplanation(BaseModel):
    constraints_considered: list[str] = Field(default_factory=list, max_length=6)
    next_action_reason: str = Field(max_length=400)
    deferred: list[str] = Field(default_factory=list, max_length=6)
    changed: str = Field(max_length=300)
    ai_used: bool
    requires_approval: bool = True


class ValidatedPlan(BaseModel):
    label: str
    summary: str
    blocks: list[CandidatePlanBlock]
    deferred_commitment_ids: list[str]
    feasibility: Literal["valid"] = "valid"


class AdaptivePlanRequest(BaseModel):
    start_at: datetime
    end_at: datetime

    @model_validator(mode="after")
    def valid_range(self):
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        if (self.end_at - self.start_at).total_seconds() > 7 * 86400:
            raise ValueError("adaptive planning is limited to seven days")
        return self


class AdaptivePlanResponse(BaseModel):
    workflow_id: str
    proposal_id: str
    recommended_plan: ValidatedPlan
    explanation: PlanExplanation
    rejected_candidate_count: int
    requires_approval: bool = True


RecoveryCause = Literal[
    "overload",
    "interruption",
    "ambiguity",
    "dependency_blocked",
    "underestimated_duration",
    "avoidance_start_friction",
    "low_available_energy",
    "calendar_disruption",
]


class RecoveryOption(BaseModel):
    action: Literal["smaller_next_step", "protect_short_block", "defer_lower_priority"]
    rationale: str = Field(min_length=3, max_length=300)
    trade_off: str = Field(min_length=3, max_length=300)
    expected_impact: str = Field(min_length=3, max_length=300)
    required_approval: bool = True
    feasible: bool = True
    feasibility_reason: str = Field(min_length=3, max_length=300)


class RecoveryModelOutput(BaseModel):
    diagnosis: RecoveryCause
    options: list[RecoveryOption] = Field(min_length=1, max_length=3)


class AdaptiveRecoveryResponse(BaseModel):
    status: str = "plan_generated"
    workflow_id: str
    diagnosis: RecoveryCause
    proposals: list[dict]
    ai_used: bool
