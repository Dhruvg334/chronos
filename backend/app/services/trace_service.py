from datetime import datetime, timezone
from typing import Any, Dict, Optional
from app.core.database import supabase_client

class AgentTraceLogger:
    def __init__(self, user_id: str, agent_run_id: str):
        self.user_id = user_id
        self.agent_run_id = agent_run_id

    def log(self, step_name: str, payload: Optional[Dict[str, Any]] = None, *, status: str = "succeeded", explanation: str = ""):
        if not supabase_client:
            return
        if payload is None:
            payload = {}
            
        data = {
            "user_id": self.user_id,
            "agent_run_id": self.agent_run_id,
            "step_name": step_name,
            "status": status,
            "explanation": explanation,
            "payload_json": payload
        }
        try:
            supabase_client.table("agent_trace_events").insert(data).execute()
        except Exception as e:
            # We don't want tracing to crash the main flow
            print(f"Failed to log trace {step_name}: {e}")

def create_agent_run(user_id: str, run_type: str = "intake", input_data: Optional[dict] = None) -> str:
    if not supabase_client:
        return ""
    data = {
        "user_id": user_id,
        "run_type": run_type,
        "status": "running",
        "input_json": input_data or {},
    }
    res = supabase_client.table("agent_runs").insert(data).execute()
    return res.data[0]["id"]

def update_agent_run(agent_run_id: str, status: str, output_data: Optional[dict] = None, error_message: Optional[str] = None):
    if not supabase_client:
        return

    update_data: Dict[str, Any] = {"status": status}
    if status in {"completed", "failed"}:
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    if output_data is not None:
        update_data["output_json"] = output_data
    if error_message is not None:
        update_data["error_message"] = error_message

    supabase_client.table("agent_runs").update(update_data).eq("id", agent_run_id).execute()
