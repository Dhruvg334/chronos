from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class CommitmentsRepository(Protocol):
    def list_for_user(self, user_id: str) -> list[dict[str, Any]]: ...
    def get_for_user(self, user_id: str, commitment_id: str) -> dict[str, Any] | None: ...
    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]: ...
    def create_tasks(self, user_id: str, rows: list[dict[str, Any]]) -> None: ...
    def create_time_spine(self, user_id: str, data: dict[str, Any]) -> None: ...


class FocusRepository(Protocol):
    def list_for_user(self, user_id: str) -> list[dict[str, Any]]: ...


class PlanningRepository(Protocol):
    def list_pending(self, user_id: str) -> list[dict[str, Any]]: ...


class ReflectionsRepository(Protocol):
    def list_recent(self, user_id: str, commitment_id: str) -> list[dict[str, Any]]: ...


class WorkflowTraceRepository(Protocol):
    def append(self, user_id: str, run_id: str, event: dict[str, Any]) -> None: ...


class GoogleConnectionRepository(Protocol):
    def get_metadata(self, user_id: str) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class RepositorySet:
    commitments: CommitmentsRepository
    focus: FocusRepository
    planning: PlanningRepository
    reflections: ReflectionsRepository
    traces: WorkflowTraceRepository
    google_connections: GoogleConnectionRepository
