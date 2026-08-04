from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_repositories
from app.core.errors import ChronosError, ErrorCode
from app.core.observability import request_id_context
from app.mcp.server import ChronosMcpServer, McpCall, ServerTool
from app.repositories.protocols import RepositorySet
from app.services.core_journey import CoreJourneyService
from app.workflows.tools import PermissionClass

router = APIRouter()


def _server(repositories: RepositorySet) -> ChronosMcpServer:
    def today(user_id, arguments): return CoreJourneyService(repositories).today(user_id).model_dump(mode="json")
    def project(user_id, arguments):
        row = repositories.projects.get_for_user(user_id, str(arguments.get("project_id", "")))
        if not row: raise ChronosError(ErrorCode.VALIDATION, "Project not found.")
        return {key: row.get(key) for key in ("id", "title", "description", "status", "target_date")}
    def approvals(user_id, arguments):
        return {"internal": repositories.planning.list_pending(user_id), "external_proposals": repositories.integrations.list_proposals(user_id)}
    def search_context(user_id, arguments):
        query = str(arguments.get("query", "")).casefold().strip()
        rows = [row for row in repositories.memory.list_for_user(user_id) if row.get("status") == "confirmed" and query in str(row.get("content", "")).casefold()]
        return {"results": [{"category": row["category"], "excerpt": str(row["content"])[:600], "source": row.get("source_reference", {}).get("label", "Confirmed memory")} for row in rows[:10]]}
    def propose_inbox(user_id, arguments):
        item = repositories.integrations.get_item(user_id, str(arguments.get("item_id", "")))
        if not item: raise ChronosError(ErrorCode.VALIDATION, "External source was not found.")
        return repositories.integrations.create_proposal(user_id, {"id": str(uuid.uuid4()), "connection_id": item["connection_id"], "integration_item_id": item["id"], "action_type": "create_reference", "target": {"kind": "reference"}, "safe_summary": str(arguments.get("summary") or item["title"])[:500], "validated_payload": {"source_item_id": item["id"], "untrusted_content": True}, "status": "pending", "approval_requirement": "explicit", "idempotency_key": str(arguments.get("idempotency_key") or uuid.uuid4())})
    return ChronosMcpServer([
        ServerTool("read_today_plan", "Read the authenticated user's bounded Today view.", PermissionClass.READ_INTERNAL, today),
        ServerTool("read_project_summary", "Read one owned project summary.", PermissionClass.READ_INTERNAL, project),
        ServerTool("list_pending_approvals", "List owned pending approvals.", PermissionClass.READ_INTERNAL, approvals),
        ServerTool("search_user_approved_context", "Search confirmed, user-approved memory.", PermissionClass.READ_INTERNAL, search_context),
        ServerTool("propose_inbox_item", "Create a reviewable Inbox proposal from an owned external item.", PermissionClass.PROPOSE_INTERNAL_WRITE, propose_inbox),
        ServerTool("propose_plan_adjustment", "Describe a plan adjustment for later approval.", PermissionClass.PROPOSE_INTERNAL_WRITE, lambda user_id, arguments: {"safe_summary": str(arguments.get("summary", ""))[:500], "persisted": False}),
    ])


@router.get("/tools")
def tools(repositories: RepositorySet = Depends(get_repositories), user_id: str = Depends(get_current_user)):
    return {"tools": _server(repositories).catalog(), "resources": ["today", "projects", "pending_approvals"], "user_scoped": bool(user_id)}


@router.post("/invoke")
def invoke(call: McpCall, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    try:
        result = _server(repositories).invoke(user_id, call)
        repositories.integrations.append_audit(user_id, {"provider": "mcp", "event_type": "tool_invocation", "outcome": result["status"], "request_id": request_id_context.get(), "safe_metadata": {"tool_name": call.tool}})
        return result
    except ChronosError:
        repositories.integrations.append_audit(user_id, {"provider": "mcp", "event_type": "permission_denial", "outcome": "denied", "request_id": request_id_context.get(), "safe_metadata": {"tool_name": call.tool}})
        raise
