from __future__ import annotations

import uuid
import copy
from datetime import datetime, timedelta
from typing import Any

from app.repositories.protocols import RepositorySet


class MemoryCommitments:
    def __init__(self, rows=None, tasks=None):
        self.rows = list(rows or [])
        self.tasks = list(tasks or [])
        self.spines: list[dict[str, Any]] = []
        self.receipts = {}
    def approve_intake(self, user_id, run_id, idempotency_key, items):
        if idempotency_key in self.receipts: return {**self.receipts[idempotency_key], "idempotent_replay": True}
        before = copy.deepcopy((self.rows, self.tasks, self.spines, getattr(self, "outcomes", MemoryOwned()).rows, getattr(self, "routines", MemoryOwned()).rows))
        try:
            for item in items:
                if item.get("kind") == "routine" and hasattr(self, "routines"):
                    self.routines.create(user_id, {"id": item["id"], "title": item["title"], "frequency_rule": "weekly", "preferred_days": item.get("preferred_days", [0,1,2,3,4]), "preferred_time": None, "minimum_viable_version": item["minimum_viable_version"], "estimated_duration_minutes": max(5, item.get("estimated_minutes") or 5), "active": True, "continuity_json": {"recent_completions": 0, "last_status": None, "last_occurrence_date": None}})
                    continue
                if item.get("kind") == "project_outcome" and hasattr(self, "outcomes"):
                    self.outcomes.create(user_id, {"id": item["id"], "project_id": item.get("project_id"), "title": item["title"], "description": item.get("description") or "", "status": "uncertain" if item.get("confidence_score", 1) < .6 else "active", "target_date": item.get("deadline_at", "")[:10] or None, "importance": item.get("importance", 3), "estimated_effort_minutes": item.get("estimated_minutes") or None, "confidence": item.get("confidence_score", .5), "completion_criteria": item["completion_criteria"], "provenance": "inbox"})
                    continue
                self.create(user_id, {key: value for key, value in item.items() if key not in {"tasks", "time_spine"}})
                self.create_tasks(user_id, [{**task, "commitment_id": item["id"]} for task in item.get("tasks", [])])
                spine = item["time_spine"]
                self.create_time_spine(user_id, {"id": spine["id"], "commitment_id": item["id"], "spine_json": spine["stages"], "current_stage": spine["current_stage"]})
        except Exception:
            self.rows, self.tasks, self.spines, outcome_rows, routine_rows = before
            if hasattr(self, "outcomes"): self.outcomes.rows = outcome_rows
            if hasattr(self, "routines"): self.routines.rows = routine_rows
            raise
        result = {"status": "success", "count": len(items), "commitment_ids": [item["id"] for item in items], "idempotent_replay": False}
        self.receipts[idempotency_key] = result
        if hasattr(self, "traces"):
            self.traces.append(user_id, run_id, {"step_name": "approval_completed", "status": "succeeded", "explanation": "Approved atomically.", "payload_json": {"count": len(items)}})
            self.traces.complete_run(user_id, run_id, {"approved_count": len(items)})
        return result
    def list_for_user(self, user_id): return [row for row in self.rows if row.get("user_id", user_id) == user_id]
    def get_for_user(self, user_id, commitment_id): return next((row for row in self.list_for_user(user_id) if str(row["id"]) == str(commitment_id)), None)
    def list_tasks_for_user(self, user_id, commitment_id=None): return [row for row in self.tasks if row.get("user_id", user_id) == user_id and (commitment_id is None or str(row.get("commitment_id")) == str(commitment_id))]
    def create(self, user_id, data):
        row = {**data, "user_id": user_id}; self.rows.append(row); return row
    def update(self, user_id, commitment_id, data):
        row = self.get_for_user(user_id, commitment_id)
        if row is None: raise RuntimeError("not found")
        row.update(data); return row
    def create_tasks(self, user_id, rows): self.tasks.extend([{**row, "user_id": user_id} for row in rows])
    def create_time_spine(self, user_id, data): self.spines.append({**data, "user_id": user_id})
    def get_time_spine(self, user_id, commitment_id): return next((row for row in self.spines if str(row["commitment_id"]) == str(commitment_id) and row["user_id"] == user_id), None)
    def update_time_spine(self, user_id, commitment_id, data):
        row = self.get_time_spine(user_id, commitment_id)
        if row: row.update(data)
        return row


class MemoryFocus:
    def __init__(self, rows=None): self.rows = list(rows or []); self.completions = {}
    def complete_transaction(self, user_id, data):
        key = data["p_idempotency_key"]
        if key in self.completions: return {**self.completions[key], "idempotent_replay": True}
        snapshot = copy.deepcopy((self.rows, self.commitments.rows, self.commitments.spines, self.reflections.rows))
        try:
            row = self.get_for_user(user_id, data["p_focus_block_id"])
            if row is None: raise RuntimeError("not found")
            row.update(status="completed", paused_at=None)
            reflection = {"id": data["p_reflection_id"], "commitment_id": row.get("commitment_id"), "focus_block_id": row["id"], "planned_minutes": int((datetime.fromisoformat(str(row["end_at"]).replace("Z", "+00:00")) - datetime.fromisoformat(str(row["start_at"]).replace("Z", "+00:00"))).total_seconds() // 60), "actual_minutes": data["p_actual_minutes"], "completion_status": data["p_completion_status"], "energy_level": data["p_energy_level"], "blocker_reason": data.get("p_blocker_reason"), "notes": data.get("p_notes")}
            self.reflections.create(user_id, reflection)
            commitment = self.commitments.get_for_user(user_id, row.get("commitment_id"))
            commitment.update(actual_minutes=int(commitment.get("actual_minutes") or 0) + data["p_actual_minutes"], progress_percent=data["p_progress_percent"], risk_score=data["p_risk_score"], risk_level=data["p_risk_level"])
            spine = self.commitments.get_time_spine(user_id, row.get("commitment_id"))
            if spine: spine.update(current_stage="reflection")
        except Exception:
            self.rows[:], self.commitments.rows[:], self.commitments.spines[:], self.reflections.rows[:] = snapshot
            raise
        result = {"status": "completed", "focus_block_id": row["id"], "commitment_id": row.get("commitment_id"), "reflection": reflection, "idempotent_replay": False}
        self.completions[key] = result; return result
    def list_for_user(self, user_id, start_at=None, end_at=None):
        rows = [row for row in self.rows if row.get("user_id", user_id) == user_id]
        if start_at: rows = [row for row in rows if datetime.fromisoformat(str(row["end_at"]).replace("Z", "+00:00")) >= start_at]
        if end_at: rows = [row for row in rows if datetime.fromisoformat(str(row["start_at"]).replace("Z", "+00:00")) <= end_at]
        return rows
    def get_for_user(self, user_id, block_id): return next((row for row in self.list_for_user(user_id) if str(row["id"]) == str(block_id)), None)
    def get_active(self, user_id): return next((row for row in self.list_for_user(user_id) if row.get("status") in {"active", "paused"}), None)
    def create(self, user_id, data):
        row = {**data, "user_id": user_id}; self.rows.append(row); return row
    def update(self, user_id, block_id, data):
        row = self.get_for_user(user_id, block_id)
        if row is None: raise RuntimeError("not found")
        row.update(data); return row


class MemoryPlanning:
    def __init__(self, events=None, proposals=None): self.events = list(events or []); self.proposals = list(proposals or []); self.approvals = {}
    def approve_recovery(self, user_id, proposal_id, idempotency_key, focus_block_id):
        if idempotency_key in self.approvals: return {**self.approvals[idempotency_key], "idempotent_replay": True}
        snapshot = copy.deepcopy((self.proposals, self.focus.rows))
        try:
            proposal = self.get_proposal(user_id, proposal_id)
            if not proposal or proposal.get("status") != "pending": raise RuntimeError("not found")
            payload = proposal.get("payload_json") or {}; created = None
            if payload.get("rescue_action_type") == "create_rescue_focus_block":
                created = self.focus.create(user_id, {"id": focus_block_id, "commitment_id": payload["commitment_id"], "title": payload.get("title", "Recovery focus"), "start_at": payload["start_at"], "end_at": payload["end_at"], "block_type": "deep_work", "status": "scheduled"})
            proposal["status"] = "approved"
        except Exception:
            self.proposals[:], self.focus.rows[:] = snapshot
            raise
        result = {"status": "approved", "action": payload.get("rescue_action_type"), "focus_block": created, "idempotent_replay": False}
        self.approvals[idempotency_key] = result; return result
    def approve_adaptive_plan(self, user_id, proposal_id, idempotency_key, block_ids):
        if idempotency_key in self.approvals: return {**self.approvals[idempotency_key], "idempotent_replay": True}
        snapshot = copy.deepcopy((self.proposals, self.focus.rows))
        try:
            proposal = self.get_proposal(user_id, proposal_id)
            if not proposal or proposal.get("status") != "pending": raise RuntimeError("not found")
            blocks = proposal["payload_json"]["adaptive_plan"]["blocks"]
            if len(blocks) != len(block_ids): raise RuntimeError("invalid block ids")
            for block, block_id in zip(blocks, block_ids):
                start = datetime.fromisoformat(str(block["start_at"]).replace("Z", "+00:00"))
                end = start + timedelta(minutes=block["duration_minutes"])
                self.focus.create(user_id, {"id": block_id, "commitment_id": block["commitment_id"], "title": block.get("rationale", "Planned focus"), "start_at": start.isoformat(), "end_at": end.isoformat(), "block_type": "deep_work", "status": "scheduled"})
            proposal["status"] = "approved"
        except Exception:
            self.proposals[:], self.focus.rows[:] = snapshot
            raise
        result = {"status": "approved", "block_ids": block_ids, "idempotent_replay": False}
        self.approvals[idempotency_key] = result; return result
    def list_pending(self, user_id): return [row for row in self.proposals if row.get("user_id", user_id) == user_id and row.get("status") == "pending"]
    def list_calendar_events(self, user_id, start_at, end_at):
        return [row for row in self.events if row.get("user_id", user_id) == user_id and datetime.fromisoformat(str(row["start_at"]).replace("Z", "+00:00")) < end_at and datetime.fromisoformat(str(row["end_at"]).replace("Z", "+00:00")) > start_at]
    def get_proposal(self, user_id, proposal_id): return next((row for row in self.proposals if str(row["id"]) == str(proposal_id) and row.get("user_id", user_id) == user_id), None)
    def create_proposal(self, user_id, data):
        row = {**data, "user_id": user_id}; self.proposals.append(row); return row
    def update_proposal(self, user_id, proposal_id, data):
        row = self.get_proposal(user_id, proposal_id)
        if row is None: raise RuntimeError("not found")
        row.update(data); return row


class MemoryReflections:
    def __init__(self): self.rows = []
    def list_recent(self, user_id, commitment_id): return [row for row in self.rows if row["user_id"] == user_id and row["commitment_id"] == commitment_id][-5:]
    def create(self, user_id, data):
        row = {**data, "user_id": user_id}; self.rows.append(row); return row


class MemoryTraces:
    def __init__(self): self.runs = {}; self.events = []
    def create_run(self, user_id, run_type, input_summary, *, workflow_id): self.runs[workflow_id] = {"id": workflow_id, "user_id": user_id, "run_type": run_type, "status": "running", "input": input_summary}; return workflow_id
    def complete_run(self, user_id, run_id, output_summary=None): self.runs[run_id].update(status="completed", output=output_summary or {})
    def fail_run(self, user_id, run_id, error_code): self.runs[run_id].update(status="failed", error_code=str(error_code))
    def append(self, user_id, run_id, event): self.events.append({**event, "user_id": user_id, "run_id": run_id})
    def list_events(self, user_id, run_id): return [event for event in self.events if event["user_id"] == user_id and event["run_id"] == run_id]


class MemoryGoogle:
    def __init__(self, state="disconnected"): self.state = state
    def get_metadata(self, user_id): return None
    def get_status(self, user_id): return {"state": self.state, "last_successful_sync": None}


class MemoryPlanningProfiles:
    DEFAULTS = {
        "timezone": "UTC", "available_weekdays": [0, 1, 2, 3, 4, 5, 6],
        "working_start_time": "09:00:00", "working_end_time": "17:00:00",
        "daily_focus_limit_minutes": 240, "default_focus_duration_minutes": 45,
        "minimum_transition_buffer_minutes": 10,
        "minimum_daily_unscheduled_buffer_minutes": 60,
        "protected_interval_start": None, "protected_interval_end": None,
        "quick_task_threshold_minutes": 5,
        "onboarding_status": "not_started", "onboarding_step": 1, "onboarding_completed_at": None,
        "planning_style": "balanced", "recommendation_frequency": "normal",
        "approval_strictness": "always_ask", "internal_write_automation_enabled": False,
        "preferred_focus_durations": [25, 45, 60], "routine_continuity_preference": "gentle",
        "quick_task_mode": "batch", "strategy_preferences": ["eisenhower_triage", "task_batching", "continuity_recovery", "focus_interval", "constrained_day", "quick_action", "time_blocking"],
        "explanation_detail": "standard",
    }
    def __init__(self, rows=None): self.rows = dict(rows or {})
    def get(self, user_id): return {**self.DEFAULTS, **self.rows.get(user_id, {})}
    def update(self, user_id, data):
        self.rows[user_id] = {**self.get(user_id), **data}; return self.rows[user_id]
    def reset(self, user_id):
        availability = {key: self.DEFAULTS[key] for key in ("timezone", "available_weekdays", "working_start_time", "working_end_time", "daily_focus_limit_minutes", "default_focus_duration_minutes", "minimum_transition_buffer_minutes", "minimum_daily_unscheduled_buffer_minutes", "protected_interval_start", "protected_interval_end", "quick_task_threshold_minutes")}
        self.rows[user_id] = {**self.get(user_id), **availability}; return self.rows[user_id]


class MemoryOwned:
    def __init__(self, rows=None): self.rows = list(rows or [])
    def list_for_user(self, user_id): return [row for row in self.rows if row.get("user_id") == user_id]
    def get_for_user(self, user_id, item_id): return next((row for row in self.list_for_user(user_id) if str(row["id"]) == str(item_id)), None)
    def create(self, user_id, data):
        row = {**data, "user_id": user_id}; self.rows.append(row); return row
    def update(self, user_id, item_id, data):
        row = self.get_for_user(user_id, item_id)
        if row is None: raise RuntimeError("not found")
        row.update(data); return row


class MemoryProjects(MemoryOwned): pass


class MemoryFeedback(MemoryOwned):
    def list_for_user(self, user_id, limit=50): return super().list_for_user(user_id)[-limit:]


class MemoryItems(MemoryOwned):
    def list_for_user(self, user_id, category=None, project_id=None):
        rows = super().list_for_user(user_id)
        if category: rows = [row for row in rows if row.get("category") == category]
        if project_id: rows = [row for row in rows if str(row.get("project_id")) == str(project_id)]
        return rows


class MemoryKnowledge:
    def __init__(self, sources=None, chunks=None):
        self.sources = list(sources or []); self.chunks = list(chunks or []); self.receipts = {}
    def list_sources(self, user_id, project_id=None):
        return [row for row in self.sources if row.get("user_id") == user_id and (project_id is None or str(row.get("project_id")) == str(project_id))]
    def get_source(self, user_id, source_id):
        return next((row for row in self.list_sources(user_id) if str(row["id"]) == str(source_id)), None)
    def create_failed_source(self, user_id, data):
        row = {**data, "user_id": user_id, "status": "failed"}; self.sources.append(row); return row
    def update_source(self, user_id, source_id, data):
        row = self.get_source(user_id, source_id)
        if row is None: raise RuntimeError("not found")
        row.update(data); return row
    def ingest(self, user_id, idempotency_key, source, chunks):
        if idempotency_key in self.receipts: return {**self.receipts[idempotency_key], "idempotent_replay": True}
        duplicate = next((row for row in self.list_sources(user_id) if row["checksum"] == source["checksum"] and row.get("project_id") == source.get("project_id") and row.get("status") != "archived"), None)
        if duplicate: result = {"status": "duplicate", "source_id": duplicate["id"], "chunk_count": 0, "idempotent_replay": False}
        else:
            row = {**source, "user_id": user_id, "status": "ready"}; self.sources.append(row)
            self.chunks.extend([{**chunk, "source_id": source["id"], "user_id": user_id, "project_id": source.get("project_id")} for chunk in chunks])
            result = {"status": "ready", "source_id": source["id"], "chunk_count": len(chunks), "idempotent_replay": False}
        self.receipts[idempotency_key] = result; return result
    def retrieve(self, user_id, query, query_embedding, project_id, limit):
        terms = set(query.casefold().split()); ranked = []
        for chunk in self.chunks:
            if chunk.get("user_id") != user_id or (project_id and str(chunk.get("project_id")) != str(project_id)): continue
            overlap = len(terms & set(chunk["content"].casefold().split()))
            source = self.get_source(user_id, chunk["source_id"])
            score = overlap + (0.2 if source and source.get("source_type") == "project_context" else 0)
            ranked.append({"chunk_id": chunk["id"], "source_id": chunk["source_id"], "project_id": chunk.get("project_id"), "title": source["title"], "source_type": source["source_type"], "excerpt": chunk["content"][:600], "score": score, "dense_rank": len(ranked)+1, "lexical_rank": 1 if overlap else None, "created_at": chunk.get("created_at")})
        return sorted(ranked, key=lambda row: (-row["score"], row["chunk_id"]))[:limit]


class MemoryContextPacks(MemoryOwned):
    pass


class MemoryOutcomes(MemoryOwned):
    def __init__(self, rows=None): super().__init__(rows); self.commitments = None
    def list_for_user(self, user_id, project_id=None):
        rows = super().list_for_user(user_id)
        return [row for row in rows if project_id is None or str(row.get("project_id")) == str(project_id)]
    def link_work(self, user_id, outcome_id, commitment_ids, task_ids):
        if self.get_for_user(user_id, outcome_id) is None: raise RuntimeError("not found")
        for row in self.commitments.list_for_user(user_id):
            if str(row.get("id")) in set(commitment_ids): row["outcome_id"] = outcome_id
        for row in self.commitments.list_tasks_for_user(user_id):
            if str(row.get("id")) in set(task_ids): row["outcome_id"] = outcome_id


class MemoryRoutines(MemoryOwned):
    def __init__(self, rows=None): super().__init__(rows); self.occurrences = []
    def upsert_occurrence(self, user_id, routine_id, data):
        existing = next((row for row in self.occurrences if row["user_id"] == user_id and str(row["routine_id"]) == str(routine_id) and str(row["occurrence_date"]) == str(data["occurrence_date"])), None)
        if existing: existing.update(data); return existing
        row = {**data, "id": str(uuid.uuid4()), "routine_id": routine_id, "user_id": user_id}; self.occurrences.append(row); return row
    def list_occurrences(self, user_id, start_at, end_at):
        return [row for row in self.occurrences if row["user_id"] == user_id and start_at.date() <= datetime.fromisoformat(str(row["occurrence_date"])).date() < end_at.date()]


class MemoryWeeklyPlans(MemoryOwned):
    def __init__(self, rows=None): super().__init__(rows); self.receipts = {}; self.focus = None
    def approve(self, user_id, plan_id, idempotency_key, block_ids):
        if idempotency_key in self.receipts: return {**self.receipts[idempotency_key], "idempotent_replay": True}
        snapshot = copy.deepcopy((self.rows, self.focus.rows))
        try:
            plan = self.get_for_user(user_id, plan_id)
            if not plan or plan.get("status") != "pending" or len(plan["proposal_json"]["blocks"]) != len(block_ids): raise RuntimeError("invalid weekly plan")
            for block, block_id in zip(plan["proposal_json"]["blocks"], block_ids):
                start = datetime.fromisoformat(str(block["start_at"]).replace("Z", "+00:00"))
                self.focus.create(user_id, {"id": block_id, "commitment_id": block["commitment_id"], "title": block["title"], "start_at": start.isoformat(), "end_at": (start + timedelta(minutes=block["duration_minutes"])).isoformat(), "block_type": "deep_work", "status": "scheduled"})
            plan["status"] = "approved"
        except Exception:
            self.rows, self.focus.rows = snapshot
            raise
        result = {"status": "approved", "block_ids": block_ids, "idempotent_replay": False}; self.receipts[idempotency_key] = result; return result


def repositories(*, commitments=None, focus=None, planning=None, reflections=None, traces=None, profiles=None, google=None, projects=None, outcomes=None, routines=None, weekly_plans=None, feedback=None, memory=None, knowledge=None, context_packs=None):
    commitments = commitments or MemoryCommitments(); focus = focus or MemoryFocus(); planning = planning or MemoryPlanning(); reflections = reflections or MemoryReflections(); traces = traces or MemoryTraces()
    commitments.traces = traces
    focus.commitments = commitments; focus.reflections = reflections
    planning.focus = focus; planning.traces = traces
    projects = projects or MemoryProjects(); outcomes = outcomes or MemoryOutcomes(); routines = routines or MemoryRoutines(); weekly_plans = weekly_plans or MemoryWeeklyPlans()
    outcomes.commitments = commitments; weekly_plans.focus = focus; commitments.outcomes = outcomes; commitments.routines = routines
    return RepositorySet(
        commitments=commitments, focus=focus, planning=planning, reflections=reflections, traces=traces,
        google_connections=google or MemoryGoogle(), planning_profiles=profiles or MemoryPlanningProfiles(),
        projects=projects, outcomes=outcomes, routines=routines, weekly_plans=weekly_plans,
        feedback=feedback or MemoryFeedback(), memory=memory or MemoryItems(),
        knowledge=knowledge or MemoryKnowledge(), context_packs=context_packs or MemoryContextPacks(),
    )
