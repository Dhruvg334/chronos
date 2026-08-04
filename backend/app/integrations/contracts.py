from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ConnectionState(StrEnum):
    CONNECTED = "connected"
    DEGRADED = "degraded"
    EXPIRED = "expired"
    REVOKED = "revoked"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class ProviderFailure(StrEnum):
    AUTH_EXPIRED = "auth_expired"
    AUTH_REVOKED = "auth_revoked"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    UNAVAILABLE = "provider_unavailable"
    INVALID_RESPONSE = "invalid_response"
    PERMISSION_DENIED = "permission_denied"


class ConnectorCapability(BaseModel):
    name: str
    permission_class: str
    required_scopes: list[str] = Field(default_factory=list)
    data_accessed: list[str] = Field(default_factory=list)
    approval_required: bool = False


class NormalizedIntegrationItem(BaseModel):
    external_id: str = Field(min_length=1, max_length=500)
    item_type: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=500)
    content_summary: str = Field(default="", max_length=4000)
    source_url: HttpUrl | None = None
    occurred_at: str | None = None
    due_at: str | None = None
    project_id: str | None = None
    checksum: str = Field(min_length=64, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)
    deleted_at: str | None = None

    @field_validator("metadata")
    @classmethod
    def allow_list_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {"calendar_id", "event_status", "recurring_event_id", "timezone", "thread_id", "repository", "number", "state", "milestone", "dependencies", "page_id", "database_id", "relative_path", "links", "plan_id", "bucket", "assignees", "selected_resource", "untrusted_content"}
        return {key: item for key, item in value.items() if key in allowed}


class SyncPage(BaseModel):
    items: list[NormalizedIntegrationItem]
    next_cursor: str | None = None
    has_more: bool = False


class ConnectorHealth(BaseModel):
    state: ConnectionState
    configured: bool
    message: str


class ExternalConnector(Protocol):
    provider: str
    capabilities: tuple[ConnectorCapability, ...]
    required_scopes: tuple[str, ...]
    def configured(self) -> bool: ...
    def authorization_url(self, user_id: str) -> str | None: ...
    def exchange_callback(self, code: str, state: str) -> dict[str, Any]: ...
    def refresh_authentication(self, user_id: str) -> ConnectionState: ...
    def revoke(self, user_id: str) -> None: ...
    def sync(self, user_id: str, cursor: str | None, *, limit: int = 100) -> SyncPage: ...
    def detail(self, user_id: str, external_id: str, *, max_chars: int = 4000) -> NormalizedIntegrationItem | None: ...
    def health(self) -> ConnectorHealth: ...
    def classify_error(self, error: Exception) -> ProviderFailure: ...


@dataclass(frozen=True)
class SyncResult:
    item_count: int
    next_cursor: str | None
    state: ConnectionState
    cached: bool = False
