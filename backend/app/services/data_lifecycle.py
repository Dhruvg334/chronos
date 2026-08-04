from __future__ import annotations

from datetime import datetime, timezone

from app.core.errors import ChronosError, ErrorCode
from app.repositories.protocols import RepositorySet


class DataLifecycleService:
    def __init__(self, repositories: RepositorySet):
        if repositories.operations is None:
            raise ChronosError(ErrorCode.CONFIGURATION, "Data controls are temporarily unavailable.")
        self.operations = repositories.operations

    def inventory(self, user_id: str) -> dict[str, object]:
        return {"generated_at": datetime.now(timezone.utc).isoformat(), "counts": self.operations.inventory(user_id)}

    def export(self, user_id: str) -> dict[str, object]:
        return {
            "format": "chronos-account-export",
            "schema_version": "1",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "data": self.operations.export(user_id),
        }

    def delete_source(self, user_id: str, source_id: str) -> dict[str, object]:
        return self.operations.delete_knowledge_source(user_id, source_id)

    def delete_account(self, user_id: str, confirmation: str) -> dict[str, object]:
        return self.operations.delete_account(user_id, confirmation)
