from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.repositories.protocols import RepositorySet


class MemoryCommitments:
    def __init__(self, rows=None, tasks=None):
        self.rows = list(rows or [])
        self.tasks = list(tasks or [])
        self.spines: list[dict[str, Any]] = []
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
    def __init__(self, rows=None): self.rows = list(rows or [])
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
    def __init__(self, events=None, proposals=None): self.events = list(events or []); self.proposals = list(proposals or [])
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
    def get_metadata(self, user_id): return None


def repositories(*, commitments=None, focus=None, planning=None, reflections=None, traces=None):
    return RepositorySet(commitments or MemoryCommitments(), focus or MemoryFocus(), planning or MemoryPlanning(), reflections or MemoryReflections(), traces or MemoryTraces(), MemoryGoogle())
