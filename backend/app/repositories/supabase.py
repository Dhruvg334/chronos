from __future__ import annotations

from typing import Any

from supabase import Client

from app.core.errors import ChronosError, ErrorCode
from app.repositories.protocols import RepositorySet


class _BaseRepository:
    def __init__(self, client: Client):
        self.client = client

    def _persistence_failure(self, operation: str, exc: Exception) -> ChronosError:
        return ChronosError(ErrorCode.PERSISTENCE, "ChronOS could not save or load this data.", context={"operation": operation, "exception": type(exc).__name__})


class SupabaseCommitmentsRepository(_BaseRepository):
    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        try:
            return self.client.table("commitments").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data or []
        except Exception as exc:
            raise self._persistence_failure("commitments.list", exc) from exc

    def get_for_user(self, user_id: str, commitment_id: str) -> dict[str, Any] | None:
        try:
            return self.client.table("commitments").select("*").eq("user_id", user_id).eq("id", commitment_id).single().execute().data
        except Exception as exc:
            raise self._persistence_failure("commitments.get", exc) from exc

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        payload = {**data, "user_id": user_id}
        try:
            result = self.client.table("commitments").insert(payload).execute().data or []
            return result[0] if result else payload
        except Exception as exc:
            raise self._persistence_failure("commitments.create", exc) from exc

    def create_tasks(self, user_id: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        try:
            self.client.table("tasks").insert([{**row, "user_id": user_id} for row in rows]).execute()
        except Exception as exc:
            raise self._persistence_failure("tasks.create", exc) from exc

    def create_time_spine(self, user_id: str, data: dict[str, Any]) -> None:
        try:
            self.client.table("time_spines").insert({**data, "user_id": user_id}).execute()
        except Exception as exc:
            raise self._persistence_failure("time_spines.create", exc) from exc


class SupabaseFocusRepository(_BaseRepository):
    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        try:
            return self.client.table("focus_blocks").select("*").eq("user_id", user_id).order("start_at").execute().data or []
        except Exception as exc:
            raise self._persistence_failure("focus.list", exc) from exc


class SupabasePlanningRepository(_BaseRepository):
    def list_pending(self, user_id: str) -> list[dict[str, Any]]:
        try:
            return self.client.table("agent_proposed_actions").select("*").eq("user_id", user_id).eq("status", "pending").execute().data or []
        except Exception as exc:
            raise self._persistence_failure("planning.list_pending", exc) from exc


class SupabaseReflectionsRepository(_BaseRepository):
    def list_recent(self, user_id: str, commitment_id: str) -> list[dict[str, Any]]:
        try:
            return self.client.table("reflections").select("*").eq("user_id", user_id).eq("commitment_id", commitment_id).order("created_at", desc=True).limit(5).execute().data or []
        except Exception as exc:
            raise self._persistence_failure("reflections.list_recent", exc) from exc


class SupabaseWorkflowTraceRepository(_BaseRepository):
    def append(self, user_id: str, run_id: str, event: dict[str, Any]) -> None:
        try:
            self.client.table("agent_trace_events").insert({**event, "user_id": user_id, "agent_run_id": run_id}).execute()
        except Exception as exc:
            raise self._persistence_failure("traces.append", exc) from exc


class SupabaseGoogleConnectionRepository(_BaseRepository):
    def get_metadata(self, user_id: str) -> dict[str, Any] | None:
        try:
            return self.client.table("google_connections").select("id, google_email, scopes, last_synced_at, expires_at").eq("user_id", user_id).single().execute().data
        except Exception:
            return None


def create_repository_set(client: Client) -> RepositorySet:
    return RepositorySet(
        commitments=SupabaseCommitmentsRepository(client),
        focus=SupabaseFocusRepository(client),
        planning=SupabasePlanningRepository(client),
        reflections=SupabaseReflectionsRepository(client),
        traces=SupabaseWorkflowTraceRepository(client),
        google_connections=SupabaseGoogleConnectionRepository(client),
    )
