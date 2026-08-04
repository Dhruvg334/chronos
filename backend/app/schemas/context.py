from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

MemoryCategory = Literal["preference", "constraint", "working_pattern", "project_fact", "personal_rule", "decision"]
MemoryStatus = Literal["proposed", "confirmed", "rejected", "archived", "expired"]
ContextPurpose = Literal["daily_planning", "weekly_planning", "project_planning", "recovery", "stuck", "reflection"]


class MemoryCreate(BaseModel):
    category: MemoryCategory
    content: str = Field(min_length=1, max_length=4000)
    project_id: str | None = None
    effective_date: date | None = None
    review_at: datetime | None = None
    expires_at: datetime | None = None


class MemoryProposal(MemoryCreate):
    source_type: Literal["reflection", "document", "project", "planning"]
    source_reference: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)


class MemoryPatch(BaseModel):
    category: MemoryCategory | None = None
    content: str | None = Field(default=None, min_length=1, max_length=4000)
    project_id: str | None = None
    effective_date: date | None = None
    review_at: datetime | None = None
    expires_at: datetime | None = None


class MemoryDecision(BaseModel):
    decision: Literal["confirm", "reject", "archive", "expire"]


class KnowledgeTextCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    source_type: Literal["note", "pasted_text", "project_context"] = "note"
    content: str = Field(min_length=1, max_length=200000)
    project_id: str | None = None
    idempotency_key: str = Field(min_length=8, max_length=160)


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    project_id: str | None = None
    purpose: ContextPurpose = "project_planning"
    limit: int = Field(default=6, ge=1, le=12)


class ContextPackRequest(BaseModel):
    purpose: ContextPurpose
    project_id: str | None = None
    commitment_id: str | None = None
    outcome_id: str | None = None
    query: str | None = Field(default=None, max_length=1000)
    token_budget: int = Field(default=1800, ge=300, le=4000)

    @model_validator(mode="after")
    def project_purpose_needs_project(self):
        if self.purpose == "project_planning" and not self.project_id:
            raise ValueError("project_id is required for project planning context")
        return self


class Citation(BaseModel):
    source_id: str
    source_title: str
    source_type: str
    excerpt: str = Field(max_length=600)
    reason_selected: str
    confidence: Literal["low", "medium", "high"]
    retrieval_method: Literal["hybrid", "memory", "structured", "history"]
    score: float = 0


class ContextPackView(BaseModel):
    id: str
    purpose: ContextPurpose
    summary: str
    token_count: int
    citations: list[Citation]
    contradictions: list[dict[str, Any]] = Field(default_factory=list)
    expires_at: datetime
    retrieval_available: bool
