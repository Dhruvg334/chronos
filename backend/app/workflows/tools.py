from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Awaitable, Callable, Generic, TypeVar

from pydantic import BaseModel

InputT = TypeVar("InputT", bound=BaseModel)
ResultT = TypeVar("ResultT", bound=BaseModel)


class PermissionClass(StrEnum):
    INTERNAL_READ = "internal_read"
    INTERNAL_WRITE = "internal_write"
    EXTERNAL_READ = "external_read"
    EXTERNAL_WRITE = "external_write"


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

    @property
    def is_write(self) -> bool:
        return self.permission in {PermissionClass.INTERNAL_WRITE, PermissionClass.EXTERNAL_WRITE}

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
