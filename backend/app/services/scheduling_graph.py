import logging
from typing import Dict, Any, List, TypedDict, Optional
from datetime import datetime, timezone, timedelta
from langgraph.graph import StateGraph, END
from postgrest.exceptions import APIError

from app.core.database import supabase_client
from app.services.scheduling_service import generate_candidate_blocks
from app.services.capacity_service import get_layered_capacity
from app.services.google_calendar_service import get_free_busy
from app.services.google_oauth_service import get_connection_status

logger = logging.getLogger(__name__)

class SchedulingState(TypedDict):
    user_id: str
    commitments: List[Dict[str, Any]]
    existing_blocks: List[Dict[str, Any]]
    busy_windows: List[Dict[str, Any]]
    capacity_slots: List[Dict[str, Any]]
    capacity_source: str
    proposals: List[Dict[str, Any]]
    trace_events: List[str]
    agent_run_id: Optional[str]
    error: Optional[str]

def load_context(state: SchedulingState) -> SchedulingState:
    user_id = state["user_id"]
    state["trace_events"].append("Loading context")
    
    try:
        # Load active/at_risk commitments
        res = supabase_client.table("commitments").select("*").eq("user_id", user_id).in_("status", ["active", "at_risk"]).execute()
        state["commitments"] = res.data or []
        
        # Load existing scheduled focus blocks from now onwards
        now = datetime.now(timezone.utc).isoformat()
        fb_res = supabase_client.table("focus_blocks").select("*").eq("user_id", user_id).in_("status", ["scheduled", "active"]).gte("end_at", now).execute()
        state["existing_blocks"] = fb_res.data or []
        
        # Load capacity
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=3) # Look 3 days ahead
        
        status = get_connection_status(user_id)
        if status.get("connected"):
            busy = get_free_busy(user_id, start_date, end_date)
            state["busy_windows"] = busy or []
            state["capacity_source"] = "google_calendar"
        else:
            state["busy_windows"] = []
            state["capacity_source"] = "mock"
        
        # Simple capacity slots generator based on business hours (mocking free time if calendar didn't provide specific blocks)
        # In a real app we'd invert busy_windows. For MVP, just assume 9-5 slots minus busy windows.
        # Actually calculate_capacity_for_range might just return total minutes. 
        # We'll create some raw slots for the scheduler to use.
        slots = []
        for i in range(3):
            day = start_date + timedelta(days=i)
            # Create a slot from 9am to 5pm
            slot_start = day.replace(hour=9, minute=0, second=0, microsecond=0)
            slot_end = day.replace(hour=17, minute=0, second=0, microsecond=0)
            if slot_end > start_date:
                actual_start = max(slot_start, start_date)
                slots.append({"start": actual_start.isoformat(), "end": slot_end.isoformat()})
                
        state["capacity_slots"] = slots
        
    except Exception as e:
        logger.error(f"Error in load_context: {e}")
        state["error"] = str(e)
        
    return state

def rank_commitments(state: SchedulingState) -> SchedulingState:
    if state.get("error"): return state
    state["trace_events"].append("Ranking commitments")
    # Actually rank_commitments is called inside generate_candidate_blocks, so we just log here.
    return state

def generate_candidate_blocks_node(state: SchedulingState) -> SchedulingState:
    if state.get("error"): return state
    state["trace_events"].append("Generating candidate blocks")
    
    proposals = generate_candidate_blocks(
        commitments=state["commitments"],
        capacity_slots=state["capacity_slots"],
        existing_blocks=state["existing_blocks"],
        busy_windows=state["busy_windows"],
        source=state["capacity_source"]
    )
    
    state["proposals"] = proposals
    return state

def validate_plan(state: SchedulingState) -> SchedulingState:
    if state.get("error"): return state
    state["trace_events"].append("Validating plan")
    # All proposals were already validated in generate_candidate_blocks loop
    return state

def persist_proposed_actions(state: SchedulingState) -> SchedulingState:
    if state.get("error"): return state
    state["trace_events"].append(f"Persisting {len(state.get('proposals', []))} proposals")
    
    try:
        # Create an agent_run
        run_res = supabase_client.table("agent_runs").insert({
            "user_id": state["user_id"],
            "agent_type": "scheduler",
            "trigger_source": "manual",
            "status": "completed"
        }).execute()
        
        agent_run_id = run_res.data[0]["id"]
        state["agent_run_id"] = agent_run_id
        
        # Insert proposals
        for prop in state.get("proposals", []):
            payload = {
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
                    "validation_status": prop["validation_status"]
                }
            }
            supabase_client.table("agent_proposed_actions").insert(payload).execute()
            
    except APIError as e:
        logger.error(f"Error persisting proposals: {e}")
        state["error"] = str(e)
        
    return state

def emit_trace(state: SchedulingState) -> SchedulingState:
    agent_run_id = state.get("agent_run_id")
    if not agent_run_id:
        return state
        
    try:
        for event in state["trace_events"]:
            supabase_client.table("agent_trace_events").insert({
                "agent_run_id": agent_run_id,
                "event_type": "info",
                "message": event
            }).execute()
            
        if state.get("error"):
            supabase_client.table("agent_trace_events").insert({
                "agent_run_id": agent_run_id,
                "event_type": "error",
                "message": state["error"]
            }).execute()
            
            supabase_client.table("agent_runs").update({
                "status": "failed",
                "error_message": state["error"]
            }).eq("id", agent_run_id).execute()
    except Exception as e:
        logger.error(f"Failed to emit trace: {e}")
        
    return state

# Construct the graph
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
    initial_state = SchedulingState(
        user_id=user_id,
        commitments=[],
        existing_blocks=[],
        busy_windows=[],
        capacity_slots=[],
        capacity_source="mock",
        proposals=[],
        trace_events=[],
        agent_run_id=None,
        error=None
    )
    
    # Run the graph (synchronously since supabase-py is sync here)
    final_state = scheduling_graph.invoke(initial_state)
    return final_state
