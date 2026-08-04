from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AccountDeleteRequest(BaseModel):
    confirmation: Literal["DELETE MY ACCOUNT"]


class KnowledgeDeleteRequest(BaseModel):
    confirmation: Literal["DELETE SOURCE"]


class OperationalStatus(BaseModel):
    status: Literal["ready", "degraded", "not_ready"]
    components: dict[str, str]
    correlation_id: str
    checked_at: str
    cache_age_seconds: float = Field(ge=0)
