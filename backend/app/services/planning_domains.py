from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.core.errors import ChronosError, ErrorCode
from app.repositories.protocols import RepositorySet
from app.schemas.planning_domains import WeeklyBlock, WeeklyDayCapacity, WeeklyProposalResponse, WeeklyView
from app.schemas.planning_profile import PlanningProfile
from app.services.capacity_engine import CapacityEngine
from app.services.core_journey import CoreJourneyService, parse_datetime, rank_commitments
from app.strategies.models import StrategyContext, StrategyPreferences
from app.strategies.selector import StrategySelector


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "user_id"}


class PlanningDomainsService:
    def __init__(self, repositories: RepositorySet):
        self.repositories = repositories
        self.capacity = CapacityEngine()

    def list_projects(self, user_id: str) -> list[dict[str, Any]]:
        outcomes = self.repositories.outcomes.list_for_user(user_id)
        commitments = self.repositories.commitments.list_for_user(user_id)
        result = []
        for project in self.repositories.projects.list_for_user(user_id):
            linked = [item for item in outcomes if str(item.get("project_id")) == str(project["id"])]
            done = sum(item.get("status") == "completed" for item in linked)
            project_commitments = [item for item in commitments if str(item.get("project_id")) == str(project["id"]) and item.get("status") != "completed"]
            next_item = rank_commitments(project_commitments)
            result.append({**_public_row(project), "outcome_count": len(linked), "completed_outcome_count": done, "progress_percent": round(done / len(linked) * 100) if linked else 0, "next_action": next_item[0].get("title") if next_item else None})
        return sorted(result, key=lambda item: ({"active": 0, "paused": 1, "completed": 2, "archived": 3}.get(item["status"], 4), item["title"].casefold()))

    def project_detail(self, user_id: str, project_id: str) -> dict[str, Any]:
        project = self.repositories.projects.get_for_user(user_id, project_id)
        if not project: raise ChronosError(ErrorCode.VALIDATION, "Project not found.")
        summary = next(item for item in self.list_projects(user_id) if str(item["id"]) == str(project_id))
        outcomes = [_public_row(item) for item in self.repositories.outcomes.list_for_user(user_id, project_id)]
        commitments = [_public_row(item) for item in self.repositories.commitments.list_for_user(user_id) if str(item.get("project_id")) == str(project_id)]
        available = [_public_row(item) for item in self.repositories.commitments.list_for_user(user_id) if not item.get("outcome_id") and item.get("status") != "completed"]
        return {**summary, "outcomes": outcomes, "linked_commitments": commitments, "available_commitments": available}

    def create_project(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return _public_row(self.repositories.projects.create(user_id, {"id": str(uuid.uuid4()), **data}))

    def update_project(self, user_id: str, project_id: str, data: dict[str, Any]) -> dict[str, Any]:
        if not self.repositories.projects.get_for_user(user_id, project_id): raise ChronosError(ErrorCode.VALIDATION, "Project not found.")
        return _public_row(self.repositories.projects.update(user_id, project_id, data))

    def create_outcome(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        project_id = data.get("project_id")
        if project_id and not self.repositories.projects.get_for_user(user_id, project_id): raise ChronosError(ErrorCode.VALIDATION, "Project not found.")
        return _public_row(self.repositories.outcomes.create(user_id, {"id": str(uuid.uuid4()), **data}))

    def update_outcome(self, user_id: str, outcome_id: str, data: dict[str, Any]) -> dict[str, Any]:
        if not self.repositories.outcomes.get_for_user(user_id, outcome_id): raise ChronosError(ErrorCode.VALIDATION, "Outcome not found.")
        if data.get("project_id") and not self.repositories.projects.get_for_user(user_id, data["project_id"]): raise ChronosError(ErrorCode.VALIDATION, "Project not found.")
        return _public_row(self.repositories.outcomes.update(user_id, outcome_id, data))

    def link_outcome_work(self, user_id: str, outcome_id: str, commitment_ids: list[str], task_ids: list[str]) -> None:
        outcome = self.repositories.outcomes.get_for_user(user_id, outcome_id)
        if not outcome: raise ChronosError(ErrorCode.VALIDATION, "Outcome not found.")
        owned_commitments = {str(item["id"]) for item in self.repositories.commitments.list_for_user(user_id)}
        owned_tasks = {str(item["id"]) for item in self.repositories.commitments.list_tasks_for_user(user_id)}
        if not set(commitment_ids) <= owned_commitments or not set(task_ids) <= owned_tasks: raise ChronosError(ErrorCode.AUTHORIZATION, "Linked work must belong to the current user.")
        self.repositories.outcomes.link_work(user_id, outcome_id, commitment_ids, task_ids)

    def list_routines(self, user_id: str, *, start: date | None = None, days: int = 7) -> list[dict[str, Any]]:
        start = start or date.today()
        persisted = {(str(row["routine_id"]), str(row["occurrence_date"])): row for row in self.repositories.routines.list_occurrences(user_id, datetime.combine(start, time.min), datetime.combine(start + timedelta(days=days), time.min))}
        result = []
        for routine in self.repositories.routines.list_for_user(user_id):
            occurrences = []
            if routine.get("active"):
                for offset in range(days):
                    day = start + timedelta(days=offset)
                    if day.weekday() in routine.get("preferred_days", []):
                        saved = persisted.get((str(routine["id"]), day.isoformat()))
                        occurrences.append({"date": day.isoformat(), "status": saved.get("status", "due") if saved else "due", "preferred_time": str(routine.get("preferred_time") or "")[:5] or None})
            continuity = routine.get("continuity_json") or {}
            result.append({**_public_row(routine), "occurrences": occurrences, "continuity_recovery": routine.get("minimum_viable_version") if continuity.get("last_status") == "skipped" else None})
        return result

    def create_routine(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return _public_row(self.repositories.routines.create(user_id, {"id": str(uuid.uuid4()), "continuity_json": {"recent_completions": 0, "last_status": None, "last_occurrence_date": None}, **data}))

    def update_routine(self, user_id: str, routine_id: str, data: dict[str, Any]) -> dict[str, Any]:
        if not self.repositories.routines.get_for_user(user_id, routine_id): raise ChronosError(ErrorCode.VALIDATION, "Routine not found.")
        return _public_row(self.repositories.routines.update(user_id, routine_id, data))

    def record_routine(self, user_id: str, routine_id: str, data: dict[str, Any]) -> dict[str, Any]:
        routine = self.repositories.routines.get_for_user(user_id, routine_id)
        if not routine: raise ChronosError(ErrorCode.VALIDATION, "Routine not found.")
        day = data["occurrence_date"]
        if day.weekday() not in routine.get("preferred_days", []): raise ChronosError(ErrorCode.CONFLICT, "That routine is not scheduled for this day.")
        occurrence = self.repositories.routines.upsert_occurrence(user_id, routine_id, {**data, "occurrence_date": day.isoformat(), "id": str(uuid.uuid4())})
        continuity = routine.get("continuity_json") or {}
        status = data["status"]
        continuity.update(last_status=status, last_occurrence_date=day.isoformat())
        if status in {"completed", "minimum_completed"}: continuity["recent_completions"] = int(continuity.get("recent_completions") or 0) + 1
        self.repositories.routines.update(user_id, routine_id, {"continuity_json": continuity})
        return _public_row(occurrence)

    def _week_context(self, user_id: str, week_start: date):
        profile = PlanningProfile.model_validate(self.repositories.planning_profiles.get(user_id))
        zone = ZoneInfo(profile.timezone)
        start_at = datetime.combine(week_start, time.min, zone)
        end_at = start_at + timedelta(days=7)
        events = self.repositories.planning.list_calendar_events(user_id, start_at, end_at)
        blocks = self.repositories.focus.list_for_user(user_id, start_at, end_at)
        calendar_state, last_sync = CoreJourneyService(self.repositories)._calendar_context(user_id, events)
        capacities = []
        for offset in range(7):
            day = week_start + timedelta(days=offset)
            result = self.capacity.calculate_day(day, profile, calendar_events=events, plan_blocks=blocks, calendar_state=calendar_state, last_successful_sync=last_sync)
            capacities.append((day, result))
        return profile, zone, start_at, end_at, events, blocks, capacities

    def weekly_view(self, user_id: str, week_start: date) -> WeeklyView:
        profile, _, start_at, end_at, _, _, capacities = self._week_context(user_id, week_start)
        projects = [item for item in self.list_projects(user_id) if item["status"] == "active"]
        outcomes = self.repositories.outcomes.list_for_user(user_id)
        due = [_public_row(item) for item in outcomes if item.get("status") not in {"completed", "archived"} and item.get("target_date") and date.fromisoformat(str(item["target_date"])) <= week_start + timedelta(days=14)]
        commitments = rank_commitments(self.repositories.commitments.list_for_user(user_id))
        scheduled = {str(row.get("commitment_id")) for row in self.repositories.focus.list_for_user(user_id, start_at, end_at) if row.get("commitment_id")}
        unscheduled = [_public_row(item) for item in commitments if str(item["id"]) not in scheduled and int(item.get("importance") or 0) >= 3]
        routine_rows = self.list_routines(user_id, start=week_start, days=7)
        total_free = sum(item.remaining_minutes for _, item in capacities)
        remaining_work = sum(max(0, int(item.get("estimated_minutes") or 0) - int(item.get("actual_minutes") or 0)) for item in commitments)
        missed = any(item.get("continuity_recovery") for item in routine_rows)
        context = StrategyContext(weekly_planning=True, recurring=missed, missed_yesterday=missed, recent_completions=1 if missed else 0, remaining_work_minutes=remaining_work, free_minutes=total_free, major_outcomes=len(due), similar_quick_tasks=sum(0 < int(item.get("estimated_minutes") or 0) <= profile.quick_task_threshold_minutes for item in commitments), needs_scheduling=bool(unscheduled), urgent=any(item.get("risk_level") in {"critical", "rescue_required"} for item in commitments), important=any(int(item.get("importance") or 0) >= 4 for item in commitments))
        strategy = StrategySelector().recommend(context, StrategyPreferences(quick_task_threshold_minutes=profile.quick_task_threshold_minutes, focus_minutes=profile.default_focus_duration_minutes))
        return WeeklyView(week_start=week_start, timezone=profile.timezone, days=[WeeklyDayCapacity(date=day, available_minutes=result.total_available_minutes, scheduled_minutes=result.scheduled_minutes, remaining_minutes=result.remaining_minutes, buffer_minutes=result.buffer_minutes, over_capacity_minutes=result.over_capacity_minutes, confidence=result.confidence, sources=list(result.sources)) for day, result in capacities], due_outcomes=due, unscheduled_work=unscheduled, routine_occurrences=[{"routine_id": item["id"], "title": item["title"], "occurrences": item["occurrences"], "continuity_recovery": item.get("continuity_recovery")} for item in routine_rows], active_projects=projects, primary_strategy=strategy.model_dump(mode="json") if strategy else None)

    def _validate_blocks(self, user_id: str, week_start: date, blocks: list[WeeklyBlock]) -> None:
        profile, zone, start_at, end_at, events, existing, capacities = self._week_context(user_id, week_start)
        commitments = {str(item["id"]): item for item in self.repositories.commitments.list_for_user(user_id)}
        outcomes = {str(item["id"]): item for item in self.repositories.outcomes.list_for_user(user_id)}
        used: list[tuple[datetime, datetime]] = []
        remaining = {day: result.remaining_minutes for day, result in capacities}
        buffer = timedelta(minutes=profile.minimum_transition_buffer_minutes)
        for block in blocks:
            commitment = commitments.get(block.commitment_id)
            if not commitment or commitment.get("status") == "blocked": raise ChronosError(ErrorCode.CONFLICT, "Blocked or unavailable work cannot be scheduled.")
            if commitment.get("outcome_id") and outcomes.get(str(commitment["outcome_id"]), {}).get("status") == "blocked": raise ChronosError(ErrorCode.CONFLICT, "Work linked to a blocked outcome cannot be scheduled.")
            start = block.start_at if block.start_at.tzinfo else block.start_at.replace(tzinfo=zone)
            end = start + timedelta(minutes=block.duration_minutes)
            local_start, local_end = start.astimezone(zone), end.astimezone(zone)
            if start < start_at or end > end_at or local_start.weekday() not in profile.available_weekdays or local_start.time() < profile.working_start_time or local_end.time() > profile.working_end_time: raise ChronosError(ErrorCode.CONFLICT, "A suggested block is outside weekly availability.")
            if profile.protected_interval_start and local_start.time() < profile.protected_interval_end and local_end.time() > profile.protected_interval_start: raise ChronosError(ErrorCode.CONFLICT, "A suggested block overlaps protected time.")
            if block.duration_minutes > remaining.get(local_start.date(), 0): raise ChronosError(ErrorCode.CONFLICT, "A suggested block exceeds daily capacity.")
            for row in [*events, *existing]:
                if row.get("status") not in {"skipped", "moved"} and parse_datetime(row["start_at"]) < end + buffer and parse_datetime(row["end_at"]) > start - buffer: raise ChronosError(ErrorCode.CONFLICT, "A suggested block overlaps existing time or its transition buffer.")
            if any(other_start < end + buffer and other_end > start - buffer for other_start, other_end in used): raise ChronosError(ErrorCode.CONFLICT, "Suggested weekly blocks overlap each other.")
            used.append((start, end)); remaining[local_start.date()] -= block.duration_minutes

    def generate_weekly_proposal(self, user_id: str, week_start: date) -> WeeklyProposalResponse:
        view = self.weekly_view(user_id, week_start)
        profile, zone, start_at, end_at, events, existing, capacities = self._week_context(user_id, week_start)
        outcomes = {str(item["id"]): item for item in self.repositories.outcomes.list_for_user(user_id)}
        projects = {str(item["id"]): item for item in self.repositories.projects.list_for_user(user_id)}
        candidates = rank_commitments(self.repositories.commitments.list_for_user(user_id))
        blocked_ids = {str(item["id"]) for item in outcomes.values() if item.get("status") == "blocked"}
        candidates = [item for item in candidates if item.get("status") != "blocked" and str(item.get("outcome_id")) not in blocked_ids]
        remaining = {day: result.remaining_minutes for day, result in capacities}
        occupied = [(parse_datetime(row["start_at"]), parse_datetime(row["end_at"])) for row in [*events, *existing] if row.get("status") not in {"skipped", "moved"}]
        blocks: list[WeeklyBlock] = []; deferred = []
        buffer = timedelta(minutes=profile.minimum_transition_buffer_minutes)
        for item in candidates:
            estimate = max(0, int(item.get("estimated_minutes") or 0) - int(item.get("actual_minutes") or 0))
            if estimate <= 0: deferred.append({"id": str(item["id"]), "title": item["title"], "reason": "Effort is uncertain."}); continue
            duration = min(estimate, profile.default_focus_duration_minutes, 180)
            found = None
            for day, _ in capacities:
                if remaining[day] < duration: continue
                cursor = datetime.combine(day, profile.working_start_time, zone)
                finish_limit = datetime.combine(day, profile.working_end_time, zone)
                while cursor + timedelta(minutes=duration) <= finish_limit:
                    finish = cursor + timedelta(minutes=duration)
                    protected = profile.protected_interval_start and cursor.time() < profile.protected_interval_end and finish.time() > profile.protected_interval_start
                    conflict = any(start < finish + buffer and end > cursor - buffer for start, end in occupied)
                    if not protected and not conflict: found = cursor; break
                    cursor += timedelta(minutes=10)
                if found: break
            if not found: deferred.append({"id": str(item["id"]), "title": item["title"], "reason": "No conflict-free capacity remained."}); continue
            block = WeeklyBlock(commitment_id=str(item["id"]), title=str(item["title"]), start_at=found, duration_minutes=duration, outcome_id=str(item["outcome_id"]) if item.get("outcome_id") else None, project_id=str(item["project_id"]) if item.get("project_id") else None)
            blocks.append(block); finish = found + timedelta(minutes=duration); occupied.append((found, finish)); remaining[found.date()] -= duration
            if len(blocks) == 5: break
        if not blocks: raise ChronosError(ErrorCode.CONFLICT, "No important work currently fits this week’s availability.")
        self._validate_blocks(user_id, week_start, blocks)
        focus_ids = []
        for block in blocks:
            outcome = outcomes.get(block.outcome_id or "")
            if outcome and str(outcome["id"]) not in {item["id"] for item in focus_ids}: focus_ids.append({"id": str(outcome["id"]), "title": outcome["title"], "project_title": projects.get(str(outcome.get("project_id")), {}).get("title")})
        explanation = {"constraints_considered": ["availability", "calendar", "protected time", "transition buffers", "daily focus limits", "outcome status"], "deferred": deferred, "summary": "ChronOS selected a small focus set that fits deterministic weekly capacity.", "ai_used": False, "requires_approval": True}
        plan = self.repositories.weekly_plans.create(user_id, {"id": str(uuid.uuid4()), "week_start": week_start.isoformat(), "status": "pending", "proposal_json": {"blocks": [item.model_dump(mode="json") for item in blocks], "focus_set": focus_ids, "deferred": deferred}, "explanation_json": explanation})
        return self._proposal_response(plan)

    def _proposal_response(self, plan: dict[str, Any]) -> WeeklyProposalResponse:
        payload = plan.get("proposal_json") or {}
        return WeeklyProposalResponse(id=str(plan["id"]), status=plan["status"], week_start=plan["week_start"], focus_set=payload.get("focus_set", []), blocks=payload.get("blocks", []), deferred=payload.get("deferred", []), explanation=plan.get("explanation_json") or {})

    def edit_weekly_proposal(self, user_id: str, plan_id: str, blocks: list[WeeklyBlock]) -> WeeklyProposalResponse:
        plan = self.repositories.weekly_plans.get_for_user(user_id, plan_id)
        if not plan or plan.get("status") != "pending": raise ChronosError(ErrorCode.CONFLICT, "Weekly proposal is no longer editable.")
        week_start = date.fromisoformat(str(plan["week_start"])); self._validate_blocks(user_id, week_start, blocks)
        payload = {**(plan.get("proposal_json") or {}), "blocks": [item.model_dump(mode="json") for item in blocks]}
        return self._proposal_response(self.repositories.weekly_plans.update(user_id, plan_id, {"proposal_json": payload}))

    def reject_weekly_proposal(self, user_id: str, plan_id: str) -> WeeklyProposalResponse:
        plan = self.repositories.weekly_plans.get_for_user(user_id, plan_id)
        if not plan or plan.get("status") != "pending": raise ChronosError(ErrorCode.CONFLICT, "Weekly proposal is no longer pending.")
        return self._proposal_response(self.repositories.weekly_plans.update(user_id, plan_id, {"status": "rejected"}))

    def approve_weekly_proposal(self, user_id: str, plan_id: str, idempotency_key: str) -> dict[str, Any]:
        plan = self.repositories.weekly_plans.get_for_user(user_id, plan_id)
        if not plan or plan.get("status") != "pending": raise ChronosError(ErrorCode.CONFLICT, "Weekly proposal is no longer pending.")
        blocks = [WeeklyBlock.model_validate(item) for item in (plan.get("proposal_json") or {}).get("blocks", [])]
        self._validate_blocks(user_id, date.fromisoformat(str(plan["week_start"])), blocks)
        return self.repositories.weekly_plans.approve(user_id, plan_id, idempotency_key, [str(uuid.uuid4()) for _ in blocks])
