from __future__ import annotations

import logging
import uuid
import re
from datetime import datetime, timezone
from typing import Any

from app.core.errors import ChronosError, ErrorCode
from app.core.versions import INTEGRATION_PROPOSAL_PROMPT_VERSION
from app.core.observability import log_event, observe_latency, record_dependency_state
from app.integrations.contracts import ConnectionState
from app.integrations.registry import ConnectorRegistry
from app.repositories.protocols import RepositorySet

logger = logging.getLogger("chronos.integrations")


class IntegrationService:
    def __init__(self, repositories: RepositorySet, registry: ConnectorRegistry) -> None:
        self.repositories = repositories; self.registry = registry

    def catalog(self, user_id: str) -> list[dict[str, Any]]:
        existing = {row["provider"]: row for row in self.repositories.integrations.list_connections(user_id)}
        result = []
        for connector in self.registry.all():
            connection = existing.get(connector.provider); health = connector.health()
            state = connection.get("status") if connection else ("disconnected" if health.configured else "unavailable")
            if connection and state == "connected" and connection.get("last_success_at"):
                try:
                    synced = datetime.fromisoformat(str(connection["last_success_at"]).replace("Z", "+00:00"))
                    if (datetime.now(timezone.utc) - synced.astimezone(timezone.utc)).total_seconds() > 86400: state = "degraded"
                except ValueError: state = "degraded"
            result.append({"provider": connector.provider, "state": state, "configured": health.configured, "read_only": True, "capabilities": [item.model_dump() for item in connector.capabilities], "requested_scopes": list(connector.required_scopes), "last_success_at": connection.get("last_success_at") if connection else None, "selected_resources": (connection.get("sync_metadata") or {}).get("selected_resources", []) if connection else [], "message": health.message if not connection else self._message(state)})
        result.append({"provider": "obsidian", "state": "available", "configured": True, "read_only": True, "capabilities": [{"name": "import_markdown", "permission_class": "read_external", "required_scopes": [], "data_accessed": ["files selected by you"], "approval_required": False}], "requested_scopes": [], "last_success_at": None, "selected_resources": [], "message": "Import only the Markdown files or ZIP you choose."})
        return result

    @staticmethod
    def _message(state: str) -> str:
        return {"connected": "Connected with read-only access.", "degraded": "Using cached context while the provider is unavailable.", "expired": "Reconnect to resume synchronization.", "revoked": "Authorization was revoked.", "error": "Synchronization needs attention.", "disconnected": "Available to connect."}.get(state, "Available to connect.")

    def sync(self, user_id: str, provider: str, *, request_id: str | None = None) -> dict[str, Any]:
        return self._sync_observed(user_id, provider, request_id=request_id)

    def _sync_observed(self, user_id: str, provider: str, *, request_id: str | None = None) -> dict[str, Any]:
        connector = self.registry.get(provider); connection = self.repositories.integrations.get_connection(user_id, provider)
        if not connector.configured(): raise ChronosError(ErrorCode.EXTERNAL_UNAVAILABLE, "This integration is not configured on the server.")
        if not connection: raise ChronosError(ErrorCode.VALIDATION, "Connect this provider before synchronizing.")
        cursor = connection.get("sync_cursor"); total = 0; pages = 0
        try:
            while pages < 10:
                with observe_latency("integration_sync_duration_ms", provider=provider):
                    page = connector.sync(user_id, cursor, limit=100)
                pages += 1
                for item in page.items:
                    payload = item.model_dump(mode="json")
                    selected = set((connection.get("sync_metadata") or {}).get("selected_resources") or [])
                    resource = next((str(payload.get("metadata", {}).get(key)) for key in ("selected_resource", "repository", "page_id", "calendar_id", "plan_id") if payload.get("metadata", {}).get(key)), None)
                    if selected and resource not in selected: continue
                    stored = self.repositories.integrations.upsert_item(user_id, connection["id"], provider, payload)
                    if item.item_type == "calendar_event": self.repositories.planning.upsert_external_calendar_event(user_id, provider, payload)
                    candidate = self._proposal_candidate(provider, stored)
                    if candidate:
                        self.repositories.integrations.create_proposal(user_id, {"id": str(uuid.uuid4()), "connection_id": connection["id"], "integration_item_id": stored["id"], "action_type": candidate["action_type"], "target": {"kind": candidate["kind"]}, "safe_summary": candidate["summary"], "validated_payload": candidate["payload"], "status": "pending", "approval_requirement": "explicit", "idempotency_key": f"sync:{provider}:{stored['external_id']}:{candidate['action_type']}"})
                    total += 1
                cursor = page.next_cursor
                if not page.has_more: break
            now = datetime.now(timezone.utc).isoformat()
            self.repositories.integrations.update_connection(user_id, connection["id"], {"status": "connected", "last_success_at": now, "last_error_at": None, "last_error_code": None, "sync_cursor": cursor})
            self.audit(user_id, provider, "synchronization", "succeeded", connection["id"], request_id, {"item_count": total, "pages": pages})
            record_dependency_state(f"integration:{provider}", "reachable")
            return {"state": "connected", "item_count": total, "cursor_advanced": bool(cursor)}
        except ChronosError: raise
        except Exception as exc:
            code = connector.classify_error(exc).value; state = "expired" if code == "auth_expired" else "revoked" if code == "auth_revoked" else "degraded"
            self.repositories.integrations.update_connection(user_id, connection["id"], {"status": state, "last_error_at": datetime.now(timezone.utc).isoformat(), "last_error_code": code})
            self.audit(user_id, provider, "provider_failure", state, connection["id"], request_id, {"error_code": code})
            log_event(logger, logging.WARNING, "integration_sync_failed", provider=provider, error_code=code)
            record_dependency_state(f"integration:{provider}", state)
            return {"state": state, "item_count": 0, "cached": True, "error_code": code}

    @staticmethod
    def _proposal_candidate(provider: str, item: dict[str, Any]) -> dict[str, Any] | None:
        text = f"{item.get('title', '')} {item.get('content_summary', '')}"
        lower = text.casefold(); action_type = None; kind = "reference"; label = "External context may be relevant"
        signals: list[str] = []
        if provider == "gmail":
            if re.search(r"\b(before|by|due|deadline|tomorrow|monday|tuesday|wednesday|thursday|friday)\b", lower): signals.append("deadline")
            if re.search(r"\b(blocked|waiting|cannot proceed|depends? on|until)\b", lower): signals.append("dependency")
            if not signals: return None
            action_type = "create_task"; kind = "task"; label = "Email appears to contain " + " and ".join(signals)
        elif provider == "github" and item.get("item_type") == "github_work": action_type = "create_task"; kind = "task"; label = "GitHub work may need review"
        elif provider == "notion": action_type = "create_reference"; label = "A selected Notion page changed"
        elif provider == "microsoft_planner": action_type = "create_task"; kind = "task"; label = "A Planner task may need review"
        if not action_type: return None
        return {"action_type": action_type, "kind": kind, "summary": f"{label}: {item['title']}"[:500], "payload": {"title": item["title"], "signals": signals, "source_excerpt": str(item.get("content_summary", ""))[:600], "source_item_id": item["id"], "untrusted_content": True}}

    def disconnect(self, user_id: str, provider: str, *, request_id: str | None = None) -> None:
        connector = self.registry.get(provider); connection = self.repositories.integrations.get_connection(user_id, provider)
        connector.revoke(user_id)
        if connection: self.repositories.integrations.update_connection(user_id, connection["id"], {"status": "revoked", "sync_cursor": None})
        self.audit(user_id, provider, "disconnection", "succeeded", connection.get("id") if connection else None, request_id, {})

    def propose(self, user_id: str, connection_id: str, item_id: str, action_type: str, summary: str, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        item = self.repositories.integrations.get_item(user_id, item_id)
        if not item or str(item["connection_id"]) != str(connection_id): raise ChronosError(ErrorCode.VALIDATION, "External source was not found.")
        proposal = self.repositories.integrations.create_proposal(user_id, {"id": str(uuid.uuid4()), "connection_id": connection_id, "integration_item_id": item_id, "action_type": action_type, "target": {"kind": action_type}, "safe_summary": summary[:500], "validated_payload": payload, "status": "pending", "approval_requirement": "explicit", "idempotency_key": idempotency_key})
        self.audit(user_id, item["provider"], "proposal_generation", "pending", connection_id, None, {"action_type": action_type, "policy_version": INTEGRATION_PROPOSAL_PROMPT_VERSION})
        return proposal

    def audit(self, user_id: str, provider: str, event_type: str, outcome: str, connection_id: str | None, request_id: str | None, metadata: dict[str, Any]) -> None:
        safe = {key: value for key, value in metadata.items() if key in {"item_count", "pages", "error_code", "action_type", "permission_class", "tool_name", "policy_version"}}
        self.repositories.integrations.append_audit(user_id, {"connection_id": connection_id, "provider": provider, "event_type": event_type, "outcome": outcome, "request_id": request_id, "safe_metadata": safe})
