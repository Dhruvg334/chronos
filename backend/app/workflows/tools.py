from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Awaitable, Callable, Generic, TypeVar

from pydantic import BaseModel

InputT = TypeVar("InputT", bound=BaseModel)
ResultT = TypeVar("ResultT", bound=BaseModel)


class PermissionClass(StrEnum):
    READ_INTERNAL = "read_internal"
    READ_EXTERNAL = "read_external"
    PROPOSE_INTERNAL_WRITE = "propose_internal_write"
    APPROVED_INTERNAL_WRITE = "approved_internal_write"
    PROPOSE_EXTERNAL_WRITE = "propose_external_write"
    APPROVED_EXTERNAL_WRITE = "approved_external_write"
    PROHIBITED = "prohibited"
    INTERNAL_READ = "read_internal"
    EXTERNAL_READ = "read_external"
    INTERNAL_WRITE = "approved_internal_write"
    EXTERNAL_WRITE = "approved_external_write"


@dataclass(frozen=True)
class ToolSpec(Generic[InputT, ResultT]):
    name: str
    description: str
    input_type: type[InputT]
    result_type: type[ResultT]
    permission: PermissionClass
    timeout_seconds: float
    idempotent: bool
    audit_category: str
    handler: Callable[[InputT], Awaitable[ResultT]]
    required_scopes: tuple[str, ...] = ()
    data_accessed: tuple[str, ...] = ()
    approval_required: bool = False
    idempotency_behavior: str = "not_applicable"
    rollback_capability: str = "none"

    @property
    def is_write(self) -> bool:
        return self.permission in {PermissionClass.APPROVED_INTERNAL_WRITE, PermissionClass.APPROVED_EXTERNAL_WRITE}

    def validate_input(self, raw: dict[str, Any]) -> InputT:
        return self.input_type.model_validate(raw)

    def validate_result(self, raw: Any) -> ResultT:
        return self.result_type.model_validate(raw)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolSpec:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ValueError(f"Unknown tool: {name}") from exc

    def all(self) -> tuple[ToolSpec, ...]:
        return tuple(self._tools.values())
