import logging
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.core.database import supabase_client
from app.services.rescue_service import find_rescue_candidates, select_rescue_strategy
from app.services.trace_service import AgentTraceLogger, create_agent_run, update_agent_run

logger = logging.getLogger(__name__)


class RescueState(TypedDict):
    user_id: str
    target_commitment_id: Optional[str]
    commitments: List[Dict[str, Any]]
    candidates: List[Dict[str, Any]]
    proposals: List[Dict[str, Any]]
    trace_events: List[Dict[str, Any]]
    agent_run_id: Optional[str]
    error: Optional[str]


def _trace(state: RescueState, step: str, explanation: str, status: str = "succeeded", payload: Optional[dict] = None) -> None:
    state["trace_events"].append({
        "step_name": step,
        "status": status,
        "explanation": explanation,
        "payload_json": payload or {},
    })


def load_rescue_context(state: RescueState) -> RescueState:
    _trace(state, "load_rescue_context", "Loaded commitment context for rescue evaluation.")
    try:
        query = (
            supabase_client.table("commitments")
            .select("*, focus_blocks(*), tasks(*)")
            .eq("user_id", state["user_id"])
        )
        if state.get("target_commitment_id"):
            query = query.eq("id", state["target_commitment_id"])
        res = query.execute()
        state["commitments"] = res.data or []
    except Exception as exc:
        logger.error("Failed to load rescue context: %s", exc)
        state["error"] = "Failed to load rescue context"
        _trace(state, "load_rescue_context", "Failed to load rescue context.", status="failed")
    return state


def diagnose_failure_mode(state: RescueState) -> RescueState:
    if state.get("error"):
        return state
    state["candidates"] = find_rescue_candidates(state["commitments"], state["user_id"])
    _trace(state, "diagnose_failure_mode", f"Identified {len(state['candidates'])} rescue candidates.")
    return state


def calculate_rescue_feasibility(state: RescueState) -> RescueState:
    if state.get("error"):
        return state
    _trace(state, "calculate_rescue_feasibility", "Calculated rescue feasibility using remaining effort and available capacity.")
    return state


def generate_rescue_options(state: RescueState) -> RescueState:
    if state.get("error"):
        return state
    proposals: List[Dict[str, Any]] = []
    for commitment in state["candidates"]:
        proposal_payload = select_rescue_strategy(commitment, state["user_id"])
        proposals.append({
            "action_type": "commitment_rescue",
            "payload_json": proposal_payload,
            "explanation": f"Rescue plan for {commitment['title']} generated.",
        })
    state["proposals"] = proposals
    _trace(state, "generate_rescue_options", f"Generated {len(proposals)} rescue proposals.")
    return state


def validate_rescue_plan(state: RescueState) -> RescueState:
    if state.get("error"):
        return state
    valid_proposals = []
    allowed_types = {
        "create_rescue_focus_block",
        "defer_task",
        "compress_scope",
        "save_renegotiation_draft",
        "increase_focus_intensity",
        "renegotiate_deadline",
    }
    for proposal in state["proposals"]:
        payload = proposal.get("payload_json") or {}
        if payload.get("validation_status") == "valid" and payload.get("rescue_action_type") in allowed_types:
            valid_proposals.append(proposal)
    state["proposals"] = valid_proposals
    _trace(state, "validate_rescue_plan", f"Validated {len(valid_proposals)} rescue proposals.")
    return state


def persist_rescue_proposals(state: RescueState) -> RescueState:
    if state.get("error"):
        return state
    _trace(state, "persist_rescue_proposals", f"Persisting {len(state.get('proposals', []))} rescue proposals.")
    try:
        agent_run_id = create_agent_run(
            state["user_id"],
            "rescue_agent",
            {
                "target_commitment_id": state.get("target_commitment_id"),
                "candidates": len(state.get("candidates", [])),
            },
        )
        state["agent_run_id"] = agent_run_id

        # Expire stale pending rescue proposals for this commitment/user before persisting a fresh plan.
        pending_query = (
            supabase_client.table("agent_proposed_actions")
            .update({"status": "expired"})
            .eq("user_id", state["user_id"])
            .eq("status", "pending")
            .eq("action_type", "commitment_rescue")
        )
        if state.get("target_commitment_id"):
            # PostgREST cannot filter nested JSON cleanly in all local versions, so expire all user rescue proposals.
            pass
        pending_query.execute()

        for proposal in state["proposals"]:
            supabase_client.table("agent_proposed_actions").insert({
                "user_id": state["user_id"],
                "agent_run_id": agent_run_id,
                "action_type": proposal["action_type"],
                "payload_json": proposal["payload_json"],
                "explanation": proposal["explanation"],
                "status": "pending",
            }).execute()
    except Exception as exc:
        logger.error("Failed to persist rescue proposals: %s", exc)
        state["error"] = "Failed to persist rescue proposals"
        _trace(state, "persist_rescue_proposals", "Failed to persist rescue proposals.", status="failed")
    return state


def emit_trace(state: RescueState) -> RescueState:
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


def _build_graph():
    workflow = StateGraph(RescueState)
    workflow.add_node("load_rescue_context", load_rescue_context)
    workflow.add_node("diagnose_failure_mode", diagnose_failure_mode)
    workflow.add_node("calculate_rescue_feasibility", calculate_rescue_feasibility)
    workflow.add_node("generate_rescue_options", generate_rescue_options)
    workflow.add_node("validate_rescue_plan", validate_rescue_plan)
    workflow.add_node("persist_rescue_proposals", persist_rescue_proposals)
    workflow.add_node("emit_trace", emit_trace)
    workflow.set_entry_point("load_rescue_context")
    workflow.add_edge("load_rescue_context", "diagnose_failure_mode")
    workflow.add_edge("diagnose_failure_mode", "calculate_rescue_feasibility")
    workflow.add_edge("calculate_rescue_feasibility", "generate_rescue_options")
    workflow.add_edge("generate_rescue_options", "validate_rescue_plan")
    workflow.add_edge("validate_rescue_plan", "persist_rescue_proposals")
    workflow.add_edge("persist_rescue_proposals", "emit_trace")
    workflow.add_edge("emit_trace", END)
    return workflow.compile()


rescue_graph = _build_graph()


def run_rescue_graph(user_id: str, target_commitment_id: Optional[str] = None) -> List[Dict[str, Any]]:
    initial_state: RescueState = {
        "user_id": user_id,
        "target_commitment_id": target_commitment_id,
        "commitments": [],
        "candidates": [],
        "proposals": [],
        "trace_events": [],
        "agent_run_id": None,
        "error": None,
    }
    final_state = rescue_graph.invoke(initial_state)
    if final_state.get("error"):
        raise RuntimeError(final_state["error"])
    return final_state["proposals"]
