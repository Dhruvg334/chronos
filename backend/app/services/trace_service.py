from datetime import datetime
from uuid import UUID
from typing import Any, Dict
from app.core.database import supabase_client

class AgentTraceLogger:
    def __init__(self, user_id: str, agent_run_id: str):
        self.user_id = user_id
        self.agent_run_id = agent_run_id

    def log(self, event_type: str, payload: Dict[str, Any] = None):
        if not supabase_client:
            return
        if payload is None:
            payload = {}
            
        data = {
            "user_id": self.user_id,
            "agent_run_id": self.agent_run_id,
            "event_type": event_type,
            "payload_json": payload
        }
        try:
            supabase_client.table("agent_trace_events").insert(data).execute()
        except Exception as e:
            # We don't want tracing to crash the main flow
            print(f"Failed to log trace {event_type}: {e}")

def create_agent_run(user_id: str, run_type: str = "intake", input_data: dict = None) -> str:
    if not supabase_client:
        return ""
    data = {
        "user_id": user_id,
        "run_type": run_type,
        "status": "running",
        "input_json": input_data or {}
    }
    res = supabase_client.table("agent_runs").insert(data).execute()
    return res.data[0]["id"]

def update_agent_run(agent_run_id: str, status: str):
    if not supabase_client:
        return
    supabase_client.table("agent_runs").update({"status": status}).eq("id", agent_run_id).execute()
