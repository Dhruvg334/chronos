from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import urlparse

from pydantic import BaseModel, Field, TypeAdapter

from app.core.errors import ChronosError, ErrorCode
from app.workflows.tools import PermissionClass


class McpRemoteTool(BaseModel):
    name: str = Field(pattern=r"^[a-zA-Z0-9_.-]{1,100}$")
    description: str = Field(max_length=500)
    input_schema: dict
    permission: PermissionClass


@dataclass(frozen=True)
class McpServerConfig:
    name: str
    endpoint: str
    allowed_tools: tuple[str, ...]
    allowed_permissions: tuple[PermissionClass, ...]
    enabled: bool = True


def validate_mcp_endpoint(endpoint: str, allowlist: tuple[str, ...]) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ChronosError(ErrorCode.AUTHORIZATION, "The MCP server endpoint is not permitted.")
    host = parsed.hostname.rstrip(".").lower()
    if host not in {value.rstrip(".").lower() for value in allowlist}:
        raise ChronosError(ErrorCode.AUTHORIZATION, "The MCP server is not allow-listed.")
    try:
        address = ipaddress.ip_address(host)
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
            raise ChronosError(ErrorCode.AUTHORIZATION, "Private-network MCP endpoints are prohibited.")
    except ValueError:
        pass
    return endpoint


class McpClientFoundation:
    def __init__(self, *, allowed_hosts: tuple[str, ...], timeout_seconds: float = 10, request_budget: int = 4) -> None:
        self.allowed_hosts = allowed_hosts; self.timeout_seconds = min(max(timeout_seconds, 1), 30); self.request_budget = min(max(request_budget, 1), 10)

    def validate_server(self, config: McpServerConfig) -> McpServerConfig:
        validate_mcp_endpoint(config.endpoint, self.allowed_hosts)
        if not config.enabled: raise ChronosError(ErrorCode.AUTHORIZATION, "This MCP server is disabled.")
        return config

    def discover(self, config: McpServerConfig, raw_tools: list[dict]) -> tuple[McpRemoteTool, ...]:
        self.validate_server(config)
        tools = TypeAdapter(list[McpRemoteTool]).validate_python(raw_tools[:100])
        accepted = []
        for tool in tools:
            if tool.name not in config.allowed_tools or tool.permission not in config.allowed_permissions: continue
            if tool.permission in {PermissionClass.APPROVED_EXTERNAL_WRITE, PermissionClass.PROHIBITED}: continue
            accepted.append(tool)
        return tuple(accepted)

    def authorize(self, config: McpServerConfig, tool: McpRemoteTool) -> str:
        self.validate_server(config)
        if tool.name not in config.allowed_tools or tool.permission not in config.allowed_permissions:
            raise ChronosError(ErrorCode.AUTHORIZATION, "The MCP tool is not permitted.")
        if tool.permission == PermissionClass.PROHIBITED:
            raise ChronosError(ErrorCode.AUTHORIZATION, "Undeclared MCP writes are prohibited.")
        if tool.permission in {PermissionClass.PROPOSE_INTERNAL_WRITE, PermissionClass.PROPOSE_EXTERNAL_WRITE}:
            return "pending_approval"
        if tool.permission in {PermissionClass.APPROVED_INTERNAL_WRITE, PermissionClass.APPROVED_EXTERNAL_WRITE}:
            raise ChronosError(ErrorCode.AUTHORIZATION, "MCP writes are proposal-only.")
        return "allowed"
