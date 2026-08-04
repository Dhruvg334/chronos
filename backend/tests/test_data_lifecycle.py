from dataclasses import replace

import pytest

from app.services.data_lifecycle import DataLifecycleService


class FakeOperations:
    def inventory(self, user_id): return {"projects": 1, "knowledge_chunks": 2}
    def export(self, user_id): return {"projects": [{"user_id": user_id, "title": "Release"}], "integration_items": []}
    def delete_knowledge_source(self, user_id, source_id): return {"status": "deleted", "chunk_count": 2}
    def delete_account(self, user_id, confirmation):
        if confirmation != "DELETE MY ACCOUNT": raise ValueError("confirmation_required")
        return {"status": "deleted", "inventory": self.inventory(user_id)}


def _repos():
    from tests.fakes import repositories
    return replace(repositories(), operations=FakeOperations())


def test_inventory_and_export_are_versioned_and_owned():
    service = DataLifecycleService(_repos())
    assert service.inventory("user-a")["counts"]["projects"] == 1
    exported = service.export("user-a")
    assert exported["schema_version"] == "1"
    assert exported["data"]["projects"][0]["user_id"] == "user-a"


def test_source_delete_reports_cascaded_chunks():
    assert DataLifecycleService(_repos()).delete_source("user-a", "source-a")["chunk_count"] == 2


def test_account_delete_requires_exact_confirmation():
    with pytest.raises(ValueError): DataLifecycleService(_repos()).delete_account("user-a", "delete")
