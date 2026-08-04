from __future__ import annotations

import hashlib
import json
from typing import Any

from app.integrations.contracts import ConnectionState, ConnectorHealth, ProviderFailure

SAFE_METADATA_KEYS = {
    "calendar_id", "event_status", "recurring_event_id", "timezone", "thread_id",
    "repository", "number", "state", "milestone", "dependencies", "page_id",
    "database_id", "relative_path", "links", "plan_id", "bucket", "assignees",
    "selected_resource", "untrusted_content",
}


def checksum(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def allow_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    result = {key: raw[key] for key in SAFE_METADATA_KEYS if key in raw}
    result["untrusted_content"] = True
    return result


class ReadOnlyConnectorBase:
    provider = "unknown"
    required_scopes: tuple[str, ...] = ()
    capabilities = ()

    def __init__(self, *, is_configured: bool = False) -> None:
        self._configured = is_configured

    def configured(self) -> bool:
        return self._configured

    def authorization_url(self, user_id: str) -> str | None:
        return None

    def exchange_callback(self, code: str, state: str) -> dict[str, Any]:
        raise RuntimeError("OAuth callback is unavailable for this connector.")

    def refresh_authentication(self, user_id: str) -> ConnectionState:
        return ConnectionState.DISCONNECTED

    def revoke(self, user_id: str) -> None:
        return None

    def health(self) -> ConnectorHealth:
        if self.configured():
            return ConnectorHealth(state=ConnectionState.DISCONNECTED, configured=True, message="Available to connect.")
        return ConnectorHealth(state=ConnectionState.DISCONNECTED, configured=False, message="Server credentials are not configured.")

    def classify_error(self, error: Exception) -> ProviderFailure:
        name = error.__class__.__name__.lower()
        message = str(error).lower()
        if "timeout" in name or "timeout" in message: return ProviderFailure.TIMEOUT
        if "429" in message or "rate" in message: return ProviderFailure.RATE_LIMITED
        if "401" in message or "expired" in message: return ProviderFailure.AUTH_EXPIRED
        if "403" in message or "revoked" in message: return ProviderFailure.AUTH_REVOKED
        return ProviderFailure.UNAVAILABLE
