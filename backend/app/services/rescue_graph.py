import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

from app.core.database import supabase_client
from app.services.rescue_service import find_rescue_candidates, select_rescue_strategy

logger = logging.getLogger(__name__)

class RescueState(TypedDict):
    user_id: str
    target_commitment_id: Optional[str]
    commitments: List[Dict[str, Any]]
    candidates: List[Dict[str, Any]]
    proposals: List[Dict[str, Any]]
    trace_events: List[Dict[str, Any]]

def load_rescue_context(state: RescueState) -> RescueState:
    logger.info("Loading rescue context")
    state["trace_events"] = []
    state["trace_events"].append({"step": "load_rescue_context", "status": "Loading commitments"})
    
    query = supabase_client.table("commitments")\
        .select("*, focus_blocks(*), tasks(*)")\
        .eq("user_id", state["user_id"])
        
    if state.get("target_commitment_id"):
        query = query.eq("id", state["target_commitment_id"])
        
    res = query.execute()
    state["commitments"] = res.data or []
    
    return state

def diagnose_failure_mode(state: RescueState) -> RescueState:
    state["trace_events"].append({"step": "diagnose_failure_mode", "status": "Finding rescue candidates"})
    state["candidates"] = find_rescue_candidates(state["commitments"], state["user_id"])
    return state

def calculate_rescue_feasibility(state: RescueState) -> RescueState:
    state["trace_events"].append({"step": "calculate_rescue_feasibility", "status": "Calculating feasibility scores"})
    # Currently handled in select_rescue_strategy directly for simplicity
    return state

def generate_rescue_options(state: RescueState) -> RescueState:
    state["trace_events"].append({"step": "generate_rescue_options", "status": "Generating options"})
    
    proposals = []
    for c in state["candidates"]:
        proposal_payload = select_rescue_strategy(c, state["user_id"])
        proposals.append({
            "action_type": "commitment_rescue",
            "payload_json": proposal_payload,
            "explanation": f"Rescue plan for {c['title']} generated."
        })
        
    state["proposals"] = proposals
    return state

def validate_rescue_plan(state: RescueState) -> RescueState:
    state["trace_events"].append({"step": "validate_rescue_plan", "status": "Validating plan"})
    # ensure no invalid proposals
    valid_proposals = []
    for p in state["proposals"]:
        if p["payload_json"]["validation_status"] == "valid":
            valid_proposals.append(p)
    state["proposals"] = valid_proposals
    return state

def persist_rescue_proposals(state: RescueState) -> RescueState:
    state["trace_events"].append({"step": "persist_rescue_proposals", "status": "Persisting to DB"})
    
    # We create a mock agent_run for tracking
    run_res = supabase_client.table("agent_runs").insert({
        "user_id": state["user_id"],
        "agent_type": "rescue_agent",
        "status": "completed"
    }).execute()
    
    if not run_res.data:
        return state
        
    run_id = run_res.data[0]["id"]
    
    # Insert proposed actions
    for p in state["proposals"]:
        supabase_client.table("agent_proposed_actions").insert({
            "user_id": state["user_id"],
            "agent_run_id": run_id,
            "action_type": p["action_type"],
            "payload_json": p["payload_json"],
            "explanation": p["explanation"],
            "status": "pending"
        }).execute()
        
    return state

def emit_trace(state: RescueState) -> RescueState:
    logger.info("Emitting traces (simulated)")
    return state

def run_rescue_graph(user_id: str, target_commitment_id: Optional[str] = None) -> List[Dict[str, Any]]:
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
    
    app = workflow.compile()
    
    initial_state = {
        "user_id": user_id,
        "target_commitment_id": target_commitment_id,
        "commitments": [],
        "candidates": [],
        "proposals": [],
        "trace_events": []
    }
    
    final_state = app.invoke(initial_state)
    return final_state["proposals"]
