from __future__ import annotations

from app.integrations.base import ReadOnlyConnectorBase
from app.integrations.contracts import ConnectorCapability, NormalizedIntegrationItem, SyncPage


class FakeConnector(ReadOnlyConnectorBase):
    def __init__(self, provider: str = "fake", items: list[NormalizedIntegrationItem] | None = None) -> None:
        super().__init__(is_configured=True)
        self.provider = provider
        self.items = list(items or [])
        self.calls: list[tuple[str, str | None]] = []
        self.capabilities = (ConnectorCapability(name="list_context", permission_class="read_external"),)

    def sync(self, user_id: str, cursor: str | None, *, limit: int = 100) -> SyncPage:
        self.calls.append((user_id, cursor))
        offset = int(cursor or 0)
        page = self.items[offset:offset + min(limit, 100)]
        next_offset = offset + len(page)
        return SyncPage(items=page, next_cursor=str(next_offset) if next_offset < len(self.items) else None, has_more=next_offset < len(self.items))

    def detail(self, user_id: str, external_id: str, *, max_chars: int = 4000) -> NormalizedIntegrationItem | None:
        item = next((item for item in self.items if item.external_id == external_id), None)
        return item.model_copy(update={"content_summary": item.content_summary[:max_chars]}) if item else None
