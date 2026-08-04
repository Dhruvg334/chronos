from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.integrations.base import ReadOnlyConnectorBase, allow_metadata, checksum
from app.integrations.contracts import ConnectorCapability, NormalizedIntegrationItem, SyncPage
from app.core.security import sanitize_external_url


def _trim_email(text: str) -> str:
    text = re.split(r"\n(?:On .+ wrote:|From:|-----Original Message-----)", text, maxsplit=1, flags=re.I)[0]
    text = re.split(r"\n--\s*\n", text, maxsplit=1)[0]
    return " ".join(text.split())[:4000]


class FixtureReadConnector(ReadOnlyConnectorBase):
    item_type = "context"
    capabilities = (ConnectorCapability(name="sync", permission_class="read_external", data_accessed=["selected external context"]),)

    def __init__(self, provider: str, scopes: tuple[str, ...], *, is_configured: bool = False, selected_resources: tuple[str, ...] = ()) -> None:
        super().__init__(is_configured=is_configured)
        self.provider = provider
        self.required_scopes = scopes
        self.selected_resources = selected_resources
        self._fixture_rows: list[dict[str, Any]] = []

    def set_fixture_rows(self, rows: list[dict[str, Any]]) -> None:
        self._fixture_rows = rows

    def normalize(self, raw: dict[str, Any]) -> NormalizedIntegrationItem:
        safe = {key: raw.get(key) for key in ("id", "title", "summary", "url", "occurred_at", "due_at", "deleted_at")}
        return NormalizedIntegrationItem(external_id=str(raw["id"]), item_type=self.item_type, title=str(raw.get("title") or "Untitled"), content_summary=str(raw.get("summary") or "")[:4000], source_url=sanitize_external_url(raw.get("url")), occurred_at=raw.get("occurred_at"), due_at=raw.get("due_at"), checksum=checksum(safe), metadata=allow_metadata(raw), deleted_at=raw.get("deleted_at"))

    def sync(self, user_id: str, cursor: str | None, *, limit: int = 100) -> SyncPage:
        if not self.configured(): raise RuntimeError("provider unavailable")
        eligible = self._fixture_rows
        if self.selected_resources:
            allowed = set(self.selected_resources)
            eligible = [row for row in eligible if str(row.get("selected_resource") or row.get("repository") or row.get("page_id") or row.get("calendar_id") or row.get("plan_id") or "") in allowed]
        offset = int(cursor or 0); bounded = min(max(limit, 1), 100)
        rows = eligible[offset:offset + bounded]
        items = [self.normalize(row) for row in rows]
        next_offset = offset + len(rows)
        return SyncPage(items=items, next_cursor=str(next_offset) if next_offset < len(eligible) else None, has_more=next_offset < len(eligible))

    def detail(self, user_id: str, external_id: str, *, max_chars: int = 4000) -> NormalizedIntegrationItem | None:
        row = next((row for row in self._fixture_rows if str(row.get("id")) == external_id), None)
        if not row: return None
        item = self.normalize(row)
        return item.model_copy(update={"content_summary": item.content_summary[:min(max_chars, 4000)]})


class GmailConnector(FixtureReadConnector):
    item_type = "email"
    def __init__(self, **kwargs): super().__init__("gmail", ("https://www.googleapis.com/auth/gmail.readonly",), **kwargs)
    def normalize(self, raw):
        body = _trim_email(str(raw.get("body") or "")); raw = {**raw, "title": raw.get("subject") or "Email", "summary": body, "thread_id": raw.get("thread_id")}
        return super().normalize(raw)


class GitHubConnector(FixtureReadConnector):
    item_type = "github_work"
    def __init__(self, **kwargs): super().__init__("github", ("metadata:read", "issues:read", "pull_requests:read",), **kwargs)


class NotionConnector(FixtureReadConnector):
    item_type = "notion_page"
    def __init__(self, **kwargs): super().__init__("notion", ("read_content",), **kwargs)


class OutlookCalendarConnector(FixtureReadConnector):
    item_type = "calendar_event"
    def __init__(self, **kwargs): super().__init__("outlook_calendar", ("Calendars.Read",), **kwargs)


class MicrosoftPlannerConnector(FixtureReadConnector):
    item_type = "planner_task"
    def __init__(self, **kwargs): super().__init__("microsoft_planner", ("Tasks.Read", "Group.Read.All"), **kwargs)


class GoogleCalendarConnector(FixtureReadConnector):
    item_type = "calendar_event"
    def __init__(self, *, auth_url=None, revoke=None, credential_loader=None, **kwargs):
        super().__init__("google_calendar", ("https://www.googleapis.com/auth/calendar.readonly",), **kwargs)
        self._auth_url = auth_url; self._revoke = revoke; self._credential_loader = credential_loader
    def authorization_url(self, user_id): return self._auth_url(user_id) if self._auth_url else None
    def revoke(self, user_id):
        if self._revoke: self._revoke(user_id)
    def sync(self, user_id, cursor, *, limit=100):
        if self._fixture_rows: return super().sync(user_id, cursor, limit=limit)
        if not self._credential_loader: return super().sync(user_id, cursor, limit=limit)
        credentials = self._credential_loader(user_id)
        if not credentials: raise RuntimeError("authorization expired")
        from googleapiclient.discovery import build
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        params = {"calendarId": "primary", "maxResults": min(max(limit, 1), 100), "singleEvents": True, "showDeleted": True}
        if cursor and cursor.startswith("sync:"): params["syncToken"] = cursor.removeprefix("sync:")
        elif cursor and cursor.startswith("page:"): params["pageToken"] = cursor.removeprefix("page:")
        response = service.events().list(**params).execute()
        items = [self.normalize(row) for row in response.get("items", [])]
        page_token = response.get("nextPageToken"); sync_token = response.get("nextSyncToken")
        next_cursor = f"page:{page_token}" if page_token else f"sync:{sync_token}" if sync_token else cursor
        return SyncPage(items=items, next_cursor=next_cursor, has_more=bool(page_token))
    def free_busy(self, user_id, time_min, time_max):
        if time_max <= time_min: raise ValueError("Invalid free/busy range.")
        credentials = self._credential_loader(user_id) if self._credential_loader else None
        if not credentials: raise RuntimeError("authorization expired")
        from googleapiclient.discovery import build
        response = build("calendar", "v3", credentials=credentials, cache_discovery=False).freebusy().query(body={"timeMin": time_min.isoformat(), "timeMax": time_max.isoformat(), "items": [{"id": "primary"}]}).execute()
        return response.get("calendars", {}).get("primary", {}).get("busy", [])
    def normalize(self, raw):
        status = raw.get("status", "confirmed")
        deleted_at = datetime.now(timezone.utc).isoformat() if status == "cancelled" else raw.get("deleted_at")
        start = raw.get("start") or {}; end = raw.get("end") or {}
        return super().normalize({**raw, "title": raw.get("summary") or "Busy", "summary": "Calendar event", "occurred_at": start.get("dateTime") or start.get("date"), "due_at": end.get("dateTime") or end.get("date"), "event_status": status, "timezone": start.get("timeZone") or raw.get("timezone"), "recurring_event_id": raw.get("recurringEventId"), "deleted_at": deleted_at})
