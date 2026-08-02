from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Generic, Protocol, Sequence, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ProviderHealth(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    UNCONFIGURED = "unconfigured"


@dataclass(frozen=True)
class ModelRequest:
    prompt: str
    system_prompt: str = ""
    model_role: str = "fast"
    max_tokens: int = 1200
    temperature: float = 0.1
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelResponse:
    text: str
    provider: str
    model: str
    request_id: str | None = None


@dataclass(frozen=True)
class StructuredResponse(Generic[T]):
    value: T
    provider: str
    model: str
    repair_attempts: int = 0


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class ToolPlan:
    tool_name: str | None
    arguments: dict[str, Any]
    decision_summary: str
    provider: str
    model: str


@dataclass(frozen=True)
class ProviderStatus:
    provider: str
    state: ProviderHealth
    configured: bool
    detail: str


class ModelGateway(Protocol):
    async def generate_text(self, request: ModelRequest) -> ModelResponse: ...

    async def generate_structured(self, request: ModelRequest, schema: type[T]) -> StructuredResponse[T]: ...

    async def select_tools(self, request: ModelRequest, tools: Sequence[ToolDefinition]) -> ToolPlan: ...

    async def health(self) -> ProviderStatus: ...

    def metadata(self) -> dict[str, str]: ...
