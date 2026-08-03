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
        before = copy.deepcopy((self.rows, self.tasks, self.spines))
        try:
            for item in items:
                self.create(user_id, {key: value for key, value in item.items() if key not in {"tasks", "time_spine"}})
                self.create_tasks(user_id, [{**task, "commitment_id": item["id"]} for task in item.get("tasks", [])])
                spine = item["time_spine"]
                self.create_time_spine(user_id, {"id": spine["id"], "commitment_id": item["id"], "spine_json": spine["stages"], "current_stage": spine["current_stage"]})
        except Exception:
            self.rows, self.tasks, self.spines = before
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
    }
    def __init__(self, rows=None): self.rows = dict(rows or {})
    def get(self, user_id): return {**self.DEFAULTS, **self.rows.get(user_id, {})}
    def update(self, user_id, data):
        self.rows[user_id] = {**self.get(user_id), **data}; return self.rows[user_id]
    def reset(self, user_id): self.rows[user_id] = self.DEFAULTS.copy(); return self.rows[user_id]


def repositories(*, commitments=None, focus=None, planning=None, reflections=None, traces=None, profiles=None, google=None):
    commitments = commitments or MemoryCommitments(); focus = focus or MemoryFocus(); planning = planning or MemoryPlanning(); reflections = reflections or MemoryReflections(); traces = traces or MemoryTraces()
    commitments.traces = traces
    focus.commitments = commitments; focus.reflections = reflections
    planning.focus = focus; planning.traces = traces
    return RepositorySet(commitments, focus, planning, reflections, traces, google or MemoryGoogle(), profiles or MemoryPlanningProfiles())
