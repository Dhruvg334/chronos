from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from supabase import Client

from app.core.errors import ChronosError, ErrorCode
from app.repositories.protocols import RepositorySet


class _BaseRepository:
    def __init__(self, client: Client):
        self.client = client

    def _failure(self, operation: str, exc: Exception) -> ChronosError:
        return ChronosError(
            ErrorCode.PERSISTENCE,
            "ChronOS could not save or load this data.",
            context={"operation": operation, "exception": type(exc).__name__},
        )


class SupabaseCommitmentsRepository(_BaseRepository):
    def approve_intake(self, user_id: str, run_id: str, idempotency_key: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        try:
            result = self.client.rpc("approve_planning_intake_transaction", {"p_user_id": user_id, "p_run_id": run_id, "p_idempotency_key": idempotency_key, "p_items": items}).execute().data
            if result.get("status") == "failed": raise RuntimeError(result.get("error_code"))
            return result
        except Exception as exc:
            raise self._failure("intake.approve_transaction", exc) from exc

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        try:
            return self.client.table("commitments").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data or []
        except Exception as exc:
            raise self._failure("commitments.list", exc) from exc

    def get_for_user(self, user_id: str, commitment_id: str) -> dict[str, Any] | None:
        try:
            rows = self.client.table("commitments").select("*").eq("user_id", user_id).eq("id", commitment_id).limit(1).execute().data or []
            return rows[0] if rows else None
        except Exception as exc:
            raise self._failure("commitments.get", exc) from exc

    def list_tasks_for_user(self, user_id: str, commitment_id: str | None = None) -> list[dict[str, Any]]:
        try:
            query = self.client.table("tasks").select("*").eq("user_id", user_id)
            if commitment_id:
                query = query.eq("commitment_id", commitment_id)
            return query.order("sequence_order").execute().data or []
        except Exception as exc:
            raise self._failure("tasks.list", exc) from exc

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("commitments").insert({**data, "user_id": user_id}).execute().data or []
            if not rows:
                raise RuntimeError("insert returned no row")
            return rows[0]
        except Exception as exc:
            raise self._failure("commitments.create", exc) from exc

    def update(self, user_id: str, commitment_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("commitments").update(data).eq("user_id", user_id).eq("id", commitment_id).execute().data or []
            if not rows:
                raise ChronosError(ErrorCode.VALIDATION, "Commitment not found.")
            return rows[0]
        except ChronosError:
            raise
        except Exception as exc:
            raise self._failure("commitments.update", exc) from exc

    def create_tasks(self, user_id: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        try:
            self.client.table("tasks").insert([{**row, "user_id": user_id} for row in rows]).execute()
        except Exception as exc:
            raise self._failure("tasks.create", exc) from exc

    def create_time_spine(self, user_id: str, data: dict[str, Any]) -> None:
        try:
            self.client.table("time_spines").insert({**data, "user_id": user_id}).execute()
        except Exception as exc:
            raise self._failure("time_spines.create", exc) from exc

    def get_time_spine(self, user_id: str, commitment_id: str) -> dict[str, Any] | None:
        try:
            rows = self.client.table("time_spines").select("*").eq("user_id", user_id).eq("commitment_id", commitment_id).limit(1).execute().data or []
            return rows[0] if rows else None
        except Exception as exc:
            raise self._failure("time_spines.get", exc) from exc

    def update_time_spine(self, user_id: str, commitment_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        try:
            rows = self.client.table("time_spines").update(data).eq("user_id", user_id).eq("commitment_id", commitment_id).execute().data or []
            return rows[0] if rows else None
        except Exception as exc:
            raise self._failure("time_spines.update", exc) from exc


class SupabaseFocusRepository(_BaseRepository):
    def complete_transaction(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            result = self.client.rpc("complete_focus_transaction", {"p_user_id": user_id, **data}).execute().data
            if result.get("status") == "failed": raise RuntimeError(result.get("error_code"))
            return result
        except Exception as exc:
            raise self._failure("focus.complete_transaction", exc) from exc

    def list_for_user(self, user_id: str, start_at: datetime | None = None, end_at: datetime | None = None) -> list[dict[str, Any]]:
        try:
            query = self.client.table("focus_blocks").select("*").eq("user_id", user_id)
            if start_at:
                query = query.gte("end_at", start_at.isoformat())
            if end_at:
                query = query.lte("start_at", end_at.isoformat())
            return query.order("start_at").execute().data or []
        except Exception as exc:
            raise self._failure("focus.list", exc) from exc

    def get_for_user(self, user_id: str, block_id: str) -> dict[str, Any] | None:
        try:
            rows = self.client.table("focus_blocks").select("*").eq("user_id", user_id).eq("id", block_id).limit(1).execute().data or []
            return rows[0] if rows else None
        except Exception as exc:
            raise self._failure("focus.get", exc) from exc

    def get_active(self, user_id: str) -> dict[str, Any] | None:
        try:
            rows = self.client.table("focus_blocks").select("*").eq("user_id", user_id).in_("status", ["active", "paused"]).order("updated_at", desc=True).limit(1).execute().data or []
            return rows[0] if rows else None
        except Exception as exc:
            raise self._failure("focus.active", exc) from exc

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("focus_blocks").insert({**data, "user_id": user_id}).execute().data or []
            if not rows:
                raise RuntimeError("insert returned no row")
            return rows[0]
        except Exception as exc:
            raise self._failure("focus.create", exc) from exc

    def update(self, user_id: str, block_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("focus_blocks").update(data).eq("user_id", user_id).eq("id", block_id).execute().data or []
            if not rows:
                raise ChronosError(ErrorCode.VALIDATION, "Focus session not found.")
            return rows[0]
        except ChronosError:
            raise
        except Exception as exc:
            raise self._failure("focus.update", exc) from exc


class SupabasePlanningRepository(_BaseRepository):
    def approve_adaptive_plan(self, user_id: str, proposal_id: str, idempotency_key: str, block_ids: list[str]) -> dict[str, Any]:
        try:
            result = self.client.rpc("approve_adaptive_plan_transaction", {
                "p_user_id": user_id,
                "p_proposal_id": proposal_id,
                "p_idempotency_key": idempotency_key,
                "p_block_ids": block_ids,
            }).execute().data
            if result.get("status") == "failed":
                raise RuntimeError(result.get("error_code"))
            return result
        except Exception as exc:
            raise self._failure("adaptive_plan.approve_transaction", exc) from exc

    def approve_recovery(self, user_id: str, proposal_id: str, idempotency_key: str, focus_block_id: str | None) -> dict[str, Any]:
        try:
            result = self.client.rpc("approve_recovery_transaction", {"p_user_id": user_id, "p_proposal_id": proposal_id, "p_idempotency_key": idempotency_key, "p_focus_block_id": focus_block_id}).execute().data
            if result.get("status") == "failed": raise RuntimeError(result.get("error_code"))
            return result
        except Exception as exc:
            raise self._failure("recovery.approve_transaction", exc) from exc

    def list_pending(self, user_id: str) -> list[dict[str, Any]]:
        try:
            return self.client.table("agent_proposed_actions").select("*").eq("user_id", user_id).eq("status", "pending").order("created_at").execute().data or []
        except Exception as exc:
            raise self._failure("planning.pending", exc) from exc

    def list_calendar_events(self, user_id: str, start_at: datetime, end_at: datetime) -> list[dict[str, Any]]:
        try:
            return self.client.table("calendar_events").select("*").eq("user_id", user_id).gte("end_at", start_at.isoformat()).lte("start_at", end_at.isoformat()).order("start_at").execute().data or []
        except Exception as exc:
            raise self._failure("calendar.list", exc) from exc

    def get_proposal(self, user_id: str, proposal_id: str) -> dict[str, Any] | None:
        try:
            rows = self.client.table("agent_proposed_actions").select("*").eq("user_id", user_id).eq("id", proposal_id).limit(1).execute().data or []
            return rows[0] if rows else None
        except Exception as exc:
            raise self._failure("planning.proposal.get", exc) from exc

    def create_proposal(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("agent_proposed_actions").insert({**data, "user_id": user_id}).execute().data or []
            if not rows:
                raise RuntimeError("insert returned no row")
            return rows[0]
        except Exception as exc:
            raise self._failure("planning.proposal.create", exc) from exc

    def update_proposal(self, user_id: str, proposal_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("agent_proposed_actions").update(data).eq("user_id", user_id).eq("id", proposal_id).execute().data or []
            if not rows:
                raise ChronosError(ErrorCode.VALIDATION, "Recovery proposal not found.")
            return rows[0]
        except ChronosError:
            raise
        except Exception as exc:
            raise self._failure("planning.proposal.update", exc) from exc


class SupabaseReflectionsRepository(_BaseRepository):
    def list_recent(self, user_id: str, commitment_id: str) -> list[dict[str, Any]]:
        try:
            return self.client.table("reflections").select("*").eq("user_id", user_id).eq("commitment_id", commitment_id).order("created_at", desc=True).limit(5).execute().data or []
        except Exception as exc:
            raise self._failure("reflections.list", exc) from exc

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("reflections").insert({**data, "user_id": user_id}).execute().data or []
            if not rows:
                raise RuntimeError("insert returned no row")
            return rows[0]
        except Exception as exc:
            raise self._failure("reflections.create", exc) from exc


class SupabaseWorkflowTraceRepository(_BaseRepository):
    def create_run(self, user_id: str, run_type: str, input_summary: dict[str, Any], *, workflow_id: str) -> str:
        payload = {"id": workflow_id, "user_id": user_id, "run_type": run_type, "status": "running", "input_json": input_summary}
        try:
            rows = self.client.table("agent_runs").insert(payload).execute().data or []
            if not rows:
                raise RuntimeError("insert returned no row")
            return str(rows[0].get("id", workflow_id))
        except Exception as exc:
            raise self._failure("workflow_runs.create", exc) from exc

    def complete_run(self, user_id: str, run_id: str, output_summary: dict[str, Any] | None = None) -> None:
        self._finish(user_id, run_id, {"status": "completed", "output_json": output_summary or {}, "completed_at": datetime.now(timezone.utc).isoformat()})

    def fail_run(self, user_id: str, run_id: str, error_code: str) -> None:
        self._finish(user_id, run_id, {"status": "failed", "error_message": error_code, "completed_at": datetime.now(timezone.utc).isoformat()})

    def _finish(self, user_id: str, run_id: str, data: dict[str, Any]) -> None:
        try:
            self.client.table("agent_runs").update(data).eq("user_id", user_id).eq("id", run_id).execute()
        except Exception as exc:
            raise self._failure("workflow_runs.finish", exc) from exc

    def append(self, user_id: str, run_id: str, event: dict[str, Any]) -> None:
        safe_event = {
            "step_name": event["step_name"],
            "tool_name": event.get("tool_name"),
            "status": event["status"],
            "explanation": event.get("explanation", ""),
            "payload_json": event.get("payload_json", {}),
        }
        try:
            self.client.table("agent_trace_events").insert({**safe_event, "user_id": user_id, "agent_run_id": run_id}).execute()
        except Exception as exc:
            raise self._failure("traces.append", exc) from exc

    def list_events(self, user_id: str, run_id: str) -> list[dict[str, Any]]:
        try:
            return self.client.table("agent_trace_events").select("*").eq("user_id", user_id).eq("agent_run_id", run_id).order("created_at").execute().data or []
        except Exception as exc:
            raise self._failure("traces.list", exc) from exc


class SupabaseGoogleConnectionRepository(_BaseRepository):
    def get_metadata(self, user_id: str) -> dict[str, Any] | None:
        try:
            rows = self.client.table("google_connections").select("id, google_email, scopes, last_synced_at, expires_at").eq("user_id", user_id).limit(1).execute().data or []
            return rows[0] if rows else None
        except Exception:
            return None

    def get_status(self, user_id: str) -> dict[str, Any]:
        try:
            rows = self.client.table("google_connections").select("google_email,last_synced_at").eq("user_id", user_id).limit(1).execute().data or []
            metadata = rows[0] if rows else None
            if metadata:
                return {"state": "connected", "last_successful_sync": metadata.get("last_synced_at"), "email": metadata.get("google_email")}
            return {"state": "disconnected", "last_successful_sync": None}
        except Exception:
            return {"state": "unavailable", "last_successful_sync": None}


PLANNING_PROFILE_COLUMNS = (
    "timezone,available_weekdays,working_start_time,working_end_time,"
    "daily_focus_limit_minutes,default_focus_duration_minutes,"
    "minimum_transition_buffer_minutes,minimum_daily_unscheduled_buffer_minutes,"
    "protected_interval_start,protected_interval_end,quick_task_threshold_minutes,"
    "onboarding_status,onboarding_step,onboarding_completed_at,planning_style,"
    "recommendation_frequency,approval_strictness,internal_write_automation_enabled,"
    "preferred_focus_durations,routine_continuity_preference,quick_task_mode,"
    "strategy_preferences,explanation_detail,updated_at"
)

PLANNING_PROFILE_DEFAULTS: dict[str, Any] = {
    "timezone": "UTC",
    "available_weekdays": [0, 1, 2, 3, 4, 5, 6],
    "working_start_time": "09:00:00",
    "working_end_time": "17:00:00",
    "daily_focus_limit_minutes": 240,
    "default_focus_duration_minutes": 45,
    "minimum_transition_buffer_minutes": 10,
    "minimum_daily_unscheduled_buffer_minutes": 60,
    "protected_interval_start": None,
    "protected_interval_end": None,
    "quick_task_threshold_minutes": 5,
}


class SupabasePlanningProfileRepository(_BaseRepository):
    def get(self, user_id: str) -> dict[str, Any]:
        try:
            rows = self.client.table("user_profiles").select(PLANNING_PROFILE_COLUMNS).eq("id", user_id).limit(1).execute().data or []
            if not rows:
                raise ChronosError(ErrorCode.VALIDATION, "Planning profile not found.")
            return rows[0]
        except ChronosError:
            raise
        except Exception as exc:
            raise self._failure("planning_profile.get", exc) from exc

    def update(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("user_profiles").update(data).eq("id", user_id).execute().data or []
            if not rows:
                raise ChronosError(ErrorCode.VALIDATION, "Planning profile not found.")
            return {key: rows[0].get(key) for key in PLANNING_PROFILE_COLUMNS.split(",")}
        except ChronosError:
            raise
        except Exception as exc:
            raise self._failure("planning_profile.update", exc) from exc

    def reset(self, user_id: str) -> dict[str, Any]:
        return self.update(user_id, PLANNING_PROFILE_DEFAULTS.copy())


class SupabaseRecommendationFeedbackRepository(_BaseRepository):
    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("recommendation_feedback").insert({**data, "user_id": user_id}).execute().data or []
            if not rows: raise RuntimeError("insert returned no row")
            return rows[0]
        except Exception as exc:
            raise self._failure("recommendation_feedback.create", exc) from exc

    def list_for_user(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        try:
            return self.client.table("recommendation_feedback").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute().data or []
        except Exception as exc:
            raise self._failure("recommendation_feedback.list", exc) from exc


class SupabaseMemoryItemsRepository(_BaseRepository):
    def list_for_user(self, user_id: str, category: str | None = None, project_id: str | None = None) -> list[dict[str, Any]]:
        try:
            query = self.client.table("memory_items").select("*").eq("user_id", user_id)
            if category: query = query.eq("category", category)
            if project_id: query = query.eq("project_id", project_id)
            return query.order("updated_at", desc=True).execute().data or []
        except Exception as exc:
            raise self._failure("memory.list", exc) from exc

    def get_for_user(self, user_id: str, memory_id: str) -> dict[str, Any] | None:
        try:
            rows = self.client.table("memory_items").select("*").eq("user_id", user_id).eq("id", memory_id).limit(1).execute().data or []
            return rows[0] if rows else None
        except Exception as exc:
            raise self._failure("memory.get", exc) from exc

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("memory_items").insert({**data, "user_id": user_id}).execute().data or []
            if not rows: raise RuntimeError("insert returned no row")
            return rows[0]
        except Exception as exc:
            raise self._failure("memory.create", exc) from exc

    def update(self, user_id: str, memory_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("memory_items").update(data).eq("user_id", user_id).eq("id", memory_id).execute().data or []
            if not rows: raise ChronosError(ErrorCode.VALIDATION, "Memory not found.")
            return rows[0]
        except ChronosError:
            raise
        except Exception as exc:
            raise self._failure("memory.update", exc) from exc


class SupabaseKnowledgeRepository(_BaseRepository):
    def list_sources(self, user_id: str, project_id: str | None = None) -> list[dict[str, Any]]:
        try:
            query = self.client.table("knowledge_sources").select("*").eq("user_id", user_id)
            if project_id: query = query.eq("project_id", project_id)
            return query.order("created_at", desc=True).execute().data or []
        except Exception as exc:
            raise self._failure("knowledge.sources", exc) from exc

    def get_source(self, user_id: str, source_id: str) -> dict[str, Any] | None:
        try:
            rows = self.client.table("knowledge_sources").select("*").eq("user_id", user_id).eq("id", source_id).limit(1).execute().data or []
            return rows[0] if rows else None
        except Exception as exc:
            raise self._failure("knowledge.source", exc) from exc

    def create_failed_source(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("knowledge_sources").insert({**data, "user_id": user_id, "status": "failed"}).execute().data or []
            if not rows: raise RuntimeError("insert returned no row")
            return rows[0]
        except Exception as exc:
            raise self._failure("knowledge.failed_source", exc) from exc

    def update_source(self, user_id: str, source_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("knowledge_sources").update(data).eq("user_id", user_id).eq("id", source_id).execute().data or []
            if not rows: raise ChronosError(ErrorCode.VALIDATION, "Knowledge source not found.")
            return rows[0]
        except ChronosError:
            raise
        except Exception as exc:
            raise self._failure("knowledge.update_source", exc) from exc

    def ingest(self, user_id: str, idempotency_key: str, source: dict[str, Any], chunks: list[dict[str, Any]]) -> dict[str, Any]:
        try:
            result = self.client.rpc("ingest_knowledge_source_transaction", {
                "p_user_id": user_id, "p_idempotency_key": idempotency_key,
                "p_source": source, "p_chunks": chunks,
            }).execute().data
            if not result or result.get("status") == "failed": raise RuntimeError((result or {}).get("error_code", "ingestion failed"))
            return result
        except Exception as exc:
            raise self._failure("knowledge.ingest_transaction", exc) from exc

    def retrieve(self, user_id: str, query: str, query_embedding: list[float], project_id: str | None, limit: int) -> list[dict[str, Any]]:
        try:
            return self.client.rpc("retrieve_knowledge_chunks", {
                "p_user_id": user_id, "p_query": query, "p_query_embedding": query_embedding,
                "p_project_id": project_id, "p_limit": limit,
            }).execute().data or []
        except Exception as exc:
            raise self._failure("knowledge.retrieve", exc) from exc


class SupabaseContextPackRepository(_BaseRepository):
    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("context_packs").insert({**data, "user_id": user_id}).execute().data or []
            if not rows: raise RuntimeError("insert returned no row")
            return rows[0]
        except Exception as exc:
            raise self._failure("context_pack.create", exc) from exc

    def get_for_user(self, user_id: str, pack_id: str) -> dict[str, Any] | None:
        try:
            rows = self.client.table("context_packs").select("*").eq("user_id", user_id).eq("id", pack_id).limit(1).execute().data or []
            return rows[0] if rows else None
        except Exception as exc:
            raise self._failure("context_pack.get", exc) from exc


class _OwnedCrudRepository(_BaseRepository):
    table_name: str
    label: str

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        try:
            return self.client.table(self.table_name).select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data or []
        except Exception as exc:
            raise self._failure(f"{self.label}.list", exc) from exc

    def get_for_user(self, user_id: str, item_id: str) -> dict[str, Any] | None:
        try:
            rows = self.client.table(self.table_name).select("*").eq("user_id", user_id).eq("id", item_id).limit(1).execute().data or []
            return rows[0] if rows else None
        except Exception as exc:
            raise self._failure(f"{self.label}.get", exc) from exc

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table(self.table_name).insert({**data, "user_id": user_id}).execute().data or []
            if not rows: raise RuntimeError("insert returned no row")
            return rows[0]
        except Exception as exc:
            raise self._failure(f"{self.label}.create", exc) from exc

    def update(self, user_id: str, item_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table(self.table_name).update(data).eq("user_id", user_id).eq("id", item_id).execute().data or []
            if not rows: raise ChronosError(ErrorCode.VALIDATION, f"{self.label.title()} not found.")
            return rows[0]
        except ChronosError:
            raise
        except Exception as exc:
            raise self._failure(f"{self.label}.update", exc) from exc


class SupabaseProjectsRepository(_OwnedCrudRepository):
    table_name = "projects"
    label = "project"


class SupabaseOutcomesRepository(_OwnedCrudRepository):
    table_name = "outcomes"
    label = "outcome"

    def list_for_user(self, user_id: str, project_id: str | None = None) -> list[dict[str, Any]]:
        try:
            query = self.client.table(self.table_name).select("*").eq("user_id", user_id)
            if project_id: query = query.eq("project_id", project_id)
            return query.order("target_date").execute().data or []
        except Exception as exc:
            raise self._failure("outcome.list", exc) from exc

    def link_work(self, user_id: str, outcome_id: str, commitment_ids: list[str], task_ids: list[str]) -> None:
        try:
            if commitment_ids:
                self.client.table("commitments").update({"outcome_id": outcome_id}).eq("user_id", user_id).in_("id", commitment_ids).execute()
            if task_ids:
                self.client.table("tasks").update({"outcome_id": outcome_id}).eq("user_id", user_id).in_("id", task_ids).execute()
        except Exception as exc:
            raise self._failure("outcome.link_work", exc) from exc


class SupabaseRoutinesRepository(_OwnedCrudRepository):
    table_name = "routines"
    label = "routine"

    def upsert_occurrence(self, user_id: str, routine_id: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            rows = self.client.table("routine_occurrences").upsert({**data, "routine_id": routine_id, "user_id": user_id}, on_conflict="routine_id,occurrence_date").execute().data or []
            if not rows: raise RuntimeError("upsert returned no row")
            return rows[0]
        except Exception as exc:
            raise self._failure("routine.occurrence", exc) from exc

    def list_occurrences(self, user_id: str, start_at: datetime, end_at: datetime) -> list[dict[str, Any]]:
        try:
            return self.client.table("routine_occurrences").select("*").eq("user_id", user_id).gte("occurrence_date", start_at.date().isoformat()).lt("occurrence_date", end_at.date().isoformat()).execute().data or []
        except Exception as exc:
            raise self._failure("routine.occurrences", exc) from exc


class SupabaseWeeklyPlansRepository(_OwnedCrudRepository):
    table_name = "weekly_plans"
    label = "weekly plan"

    def approve(self, user_id: str, plan_id: str, idempotency_key: str, block_ids: list[str]) -> dict[str, Any]:
        try:
            result = self.client.rpc("approve_weekly_plan_transaction", {"p_user_id": user_id, "p_plan_id": plan_id, "p_idempotency_key": idempotency_key, "p_block_ids": block_ids}).execute().data
            if result.get("status") == "failed": raise RuntimeError(result.get("error_code"))
            return result
        except Exception as exc:
            raise self._failure("weekly_plan.approve_transaction", exc) from exc


def create_repository_set(client: Client) -> RepositorySet:
    return RepositorySet(
        commitments=SupabaseCommitmentsRepository(client),
        focus=SupabaseFocusRepository(client),
        planning=SupabasePlanningRepository(client),
        reflections=SupabaseReflectionsRepository(client),
        traces=SupabaseWorkflowTraceRepository(client),
        google_connections=SupabaseGoogleConnectionRepository(client),
        planning_profiles=SupabasePlanningProfileRepository(client),
        projects=SupabaseProjectsRepository(client),
        outcomes=SupabaseOutcomesRepository(client),
        routines=SupabaseRoutinesRepository(client),
        weekly_plans=SupabaseWeeklyPlansRepository(client),
        feedback=SupabaseRecommendationFeedbackRepository(client),
        memory=SupabaseMemoryItemsRepository(client),
        knowledge=SupabaseKnowledgeRepository(client),
        context_packs=SupabaseContextPackRepository(client),
    )
