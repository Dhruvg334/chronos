from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, Field

from app.core.errors import ChronosError, ErrorCode
from app.workflows.tools import PermissionClass


class McpCall(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class ServerTool:
    name: str
    description: str
    permission: PermissionClass
    handler: Callable[[str, dict[str, Any]], dict[str, Any]]


class ChronosMcpServer:
    """Authenticated, application-service tools only; never exposes tables or SQL."""
    def __init__(self, tools: list[ServerTool] | None = None) -> None:
        self.tools = {tool.name: tool for tool in tools or []}

    def catalog(self) -> list[dict[str, Any]]:
        return [{"name": tool.name, "description": tool.description, "permission": tool.permission.value} for tool in self.tools.values()]

    def invoke(self, user_id: str, call: McpCall) -> dict[str, Any]:
        tool = self.tools.get(call.tool)
        if not tool: raise ChronosError(ErrorCode.AUTHORIZATION, "The requested MCP tool is unavailable.")
        if tool.permission in {PermissionClass.APPROVED_INTERNAL_WRITE, PermissionClass.APPROVED_EXTERNAL_WRITE, PermissionClass.PROHIBITED}:
            raise ChronosError(ErrorCode.AUTHORIZATION, "Direct MCP writes are prohibited.")
        result = tool.handler(user_id, call.arguments)
        if tool.permission in {PermissionClass.PROPOSE_INTERNAL_WRITE, PermissionClass.PROPOSE_EXTERNAL_WRITE}:
            return {"status": "pending_approval", "proposal": result}
        return {"status": "succeeded", "result": result}
