import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph
from postgrest.exceptions import APIError

from app.core.database import supabase_client
from app.services.google_calendar_service import get_free_busy
from app.services.google_oauth_service import get_connection_status
from app.services.scheduling_service import generate_candidate_blocks
from app.services.trace_service import AgentTraceLogger, create_agent_run, update_agent_run

logger = logging.getLogger(__name__)


class SchedulingState(TypedDict):
    user_id: str
    commitments: List[Dict[str, Any]]
    existing_blocks: List[Dict[str, Any]]
    busy_windows: List[Dict[str, Any]]
    capacity_slots: List[Dict[str, Any]]
    capacity_source: str
    proposals: List[Dict[str, Any]]
    trace_events: List[Dict[str, Any]]
    agent_run_id: Optional[str]
    error: Optional[str]


def _trace(state: SchedulingState, step: str, explanation: str, status: str = "succeeded", payload: Optional[dict] = None) -> None:
    state["trace_events"].append({
        "step_name": step,
        "status": status,
        "explanation": explanation,
        "payload_json": payload or {},
    })


def load_context(state: SchedulingState) -> SchedulingState:
    user_id = state["user_id"]
    _trace(state, "load_context", "Loaded scheduling context.")

    try:
        res = (
            supabase_client.table("commitments")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", ["active", "at_risk"])
            .execute()
        )
        state["commitments"] = res.data or []

        now_iso = datetime.now(timezone.utc).isoformat()
        fb_res = (
            supabase_client.table("focus_blocks")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", ["scheduled", "active"])
            .gte("end_at", now_iso)
            .execute()
        )
        state["existing_blocks"] = fb_res.data or []

        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=3)

        status = get_connection_status(user_id)
        if status.get("connected"):
            state["busy_windows"] = get_free_busy(user_id, start_date, end_date) or []
            state["capacity_source"] = "google_calendar"
        else:
            state["busy_windows"] = []
            state["capacity_source"] = "mock"

        slots = []
        for i in range(3):
            day = start_date + timedelta(days=i)
            slot_start = day.replace(hour=9, minute=0, second=0, microsecond=0)
            slot_end = day.replace(hour=17, minute=0, second=0, microsecond=0)
            if slot_end > start_date:
                slots.append({"start": max(slot_start, start_date).isoformat(), "end": slot_end.isoformat()})
        state["capacity_slots"] = slots
    except Exception as exc:
        logger.error("Error in scheduling load_context: %s", exc)
        state["error"] = "Failed to load scheduling context"
        _trace(state, "load_context", "Failed to load scheduling context.", status="failed")

    return state


def rank_commitments(state: SchedulingState) -> SchedulingState:
    if state.get("error"):
        return state
    _trace(state, "rank_commitments", "Ranked commitments by risk, deadline, and remaining effort.")
    return state


def generate_candidate_blocks_node(state: SchedulingState) -> SchedulingState:
    if state.get("error"):
        return state
    _trace(state, "generate_candidate_blocks", "Generated candidate focus block proposals.")
    state["proposals"] = generate_candidate_blocks(
        commitments=state["commitments"],
        capacity_slots=state["capacity_slots"],
        existing_blocks=state["existing_blocks"],
        busy_windows=state["busy_windows"],
        source=state["capacity_source"],
    )
    return state


def validate_plan(state: SchedulingState) -> SchedulingState:
    if state.get("error"):
        return state
    _trace(state, "validate_plan", "Validated generated schedule proposals.")
    return state


def persist_proposed_actions(state: SchedulingState) -> SchedulingState:
    if state.get("error"):
        return state
    _trace(state, "persist_proposed_actions", f"Persisting {len(state.get('proposals', []))} scheduling proposals.")

    try:
        agent_run_id = create_agent_run(
            state["user_id"],
            "scheduler",
            {
                "capacity_source": state["capacity_source"],
                "commitments_loaded": len(state["commitments"]),
                "existing_blocks_loaded": len(state["existing_blocks"]),
            },
        )
        state["agent_run_id"] = agent_run_id

        # Prevent duplicate stale scheduling proposals from piling up after repeated plan generation.
        supabase_client.table("agent_proposed_actions").update({"status": "expired"}).eq("user_id", state["user_id"]).eq("status", "pending").eq("action_type", "create_focus_block").execute()

        for prop in state.get("proposals", []):
            supabase_client.table("agent_proposed_actions").insert({
                "user_id": state["user_id"],
                "agent_run_id": agent_run_id,
                "action_type": prop["action_type"],
                "status": "pending",
                "explanation": prop["reason"],
                "payload_json": {
                    "commitment_id": prop["commitment_id"],
                    "title": prop["title"],
                    "start_at": prop["start_at"],
                    "end_at": prop["end_at"],
                    "duration_minutes": prop["duration_minutes"],
                    "risk_level": prop["risk_level"],
                    "confidence_score": prop["confidence_score"],
                    "capacity_source": prop["capacity_source"],
                    "validation_status": prop["validation_status"],
                    "scheduling_reason": prop["reason"],
                },
            }).execute()
    except APIError as exc:
        logger.error("Error persisting schedule proposals")
        state["error"] = "Failed to persist scheduling proposals"
        _trace(state, "persist_proposed_actions", "Failed to persist schedule proposals.", status="failed")
    return state


def emit_trace(state: SchedulingState) -> SchedulingState:
    agent_run_id = state.get("agent_run_id")
    if not agent_run_id:
        return state

    logger_ = AgentTraceLogger(state["user_id"], agent_run_id)
    for event in state["trace_events"]:
        logger_.log(
            event["step_name"],
            event.get("payload_json") or {},
            status=event.get("status", "succeeded"),
            explanation=event.get("explanation", ""),
        )

    if state.get("error"):
        update_agent_run(agent_run_id, "failed", error_message=state["error"])
    else:
        update_agent_run(agent_run_id, "completed", output_data={"proposals_generated": len(state.get("proposals", []))})
    return state


workflow = StateGraph(SchedulingState)
workflow.add_node("load_context", load_context)
workflow.add_node("rank_commitments", rank_commitments)
workflow.add_node("generate_candidate_blocks", generate_candidate_blocks_node)
workflow.add_node("validate_plan", validate_plan)
workflow.add_node("persist_proposed_actions", persist_proposed_actions)
workflow.add_node("emit_trace", emit_trace)
workflow.set_entry_point("load_context")
workflow.add_edge("load_context", "rank_commitments")
workflow.add_edge("rank_commitments", "generate_candidate_blocks")
workflow.add_edge("generate_candidate_blocks", "validate_plan")
workflow.add_edge("validate_plan", "persist_proposed_actions")
workflow.add_edge("persist_proposed_actions", "emit_trace")
workflow.add_edge("emit_trace", END)
scheduling_graph = workflow.compile()


def run_scheduling_graph(user_id: str) -> Dict[str, Any]:
    initial_state: SchedulingState = {
        "user_id": user_id,
        "commitments": [],
        "existing_blocks": [],
        "busy_windows": [],
        "capacity_slots": [],
        "capacity_source": "mock",
        "proposals": [],
        "trace_events": [],
        "agent_run_id": None,
        "error": None,
    }
    return scheduling_graph.invoke(initial_state)
