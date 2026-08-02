from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional

from app.repositories.protocols import WorkflowTraceRepository

logger = logging.getLogger("uvicorn.error")


def _compact_error(error: Exception) -> str:
    message = str(error)
    if len(message) > 240:
        return message[:237] + "..."
    return message


class AgentTraceLogger:
    def __init__(self, user_id: str, agent_run_id: str, repository: WorkflowTraceRepository | None = None):
        self.user_id = user_id
        self.agent_run_id = agent_run_id
        self.repository = repository

    def log(
        self,
        step_name: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        status: str = "succeeded",
        explanation: str = "",
    ) -> bool:
        if not self.repository or not self.agent_run_id:
            return False
        if payload is None:
            payload = {}

        data = {
            "step_name": step_name,
            "status": status,
            "explanation": explanation,
            "payload_json": payload,
        }
        try:
            self.repository.append(self.user_id, self.agent_run_id, data)
            return True
        except Exception as exc:
            logger.warning("Trace write skipped for %s: %s", step_name, _compact_error(exc))
            return False


def create_agent_run(user_id: str, run_type: str = "intake", input_data: Optional[dict] = None, repository: WorkflowTraceRepository | None = None) -> str:
    if not repository:
        return ""

    try:
        import uuid
        workflow_id = str(uuid.uuid4())
        return repository.create_run(user_id, run_type, input_data or {}, workflow_id=workflow_id)
    except Exception as exc:
        logger.warning("Agent run creation skipped: %s", _compact_error(exc))
        return ""


def update_agent_run(
    agent_run_id: str,
    status: str,
    output_data: Optional[dict] = None,
    error_message: Optional[str] = None,
    repository: WorkflowTraceRepository | None = None,
    user_id: str | None = None,
) -> bool:
    if not repository or not agent_run_id or not user_id:
        return False

    try:
        if status == "completed": repository.complete_run(user_id, agent_run_id, output_data)
        elif status == "failed": repository.fail_run(user_id, agent_run_id, error_message or "workflow_failed")
        else: return False
        return True
    except Exception as exc:
        logger.warning("Agent run update skipped for %s: %s", agent_run_id, _compact_error(exc))
        return False
