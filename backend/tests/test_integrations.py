import uuid
from pathlib import Path

from app.integrations.contracts import NormalizedIntegrationItem
from app.integrations.fake import FakeConnector
from app.integrations.registry import ConnectorRegistry
from app.integrations.service import IntegrationService
from tests.fakes import MemoryIntegrations, repositories


def connection(repo, provider="gmail", user="u1"):
    return repo.create_connection(user, {"id": str(uuid.uuid4()), "provider": provider, "status": "connected", "sync_cursor": None, "sync_metadata": {}})


def test_sync_is_idempotent_bounded_and_audited_without_content():
    store = MemoryIntegrations(); conn = connection(store)
    item = NormalizedIntegrationItem(external_id="m1", item_type="email", title="Deadline", content_summary="Finish by tomorrow", checksum="a" * 64)
    service = IntegrationService(repositories(integrations=store), ConnectorRegistry([FakeConnector("gmail", [item])]))
    first = service.sync("u1", "gmail", request_id="req-1"); second = service.sync("u1", "gmail", request_id="req-2")
    assert first["item_count"] == second["item_count"] == 1
    assert len(store.items) == 1
    assert store.audit[-1]["safe_metadata"] == {"item_count": 1, "pages": 1}
    assert "Finish by tomorrow" not in str(store.audit)
    assert conn["status"] == "connected"


def test_provider_failure_keeps_cached_items_and_marks_degraded():
    class Broken(FakeConnector):
        def sync(self, *args, **kwargs): raise TimeoutError("private response")
    store = MemoryIntegrations(); conn = connection(store); store.items.append({"id":"i1","user_id":"u1","connection_id":conn["id"],"provider":"gmail","external_id":"m1","title":"Cached","deleted_at":None})
    result = IntegrationService(repositories(integrations=store), ConnectorRegistry([Broken("gmail")])).sync("u1", "gmail")
    assert result == {"state": "degraded", "item_count": 0, "cached": True, "error_code": "timeout"}
    assert store.list_items("u1")[0]["title"] == "Cached"


def test_cross_user_item_and_proposal_lookup_is_denied_by_repository_boundary():
    store = MemoryIntegrations(); conn = connection(store)
    row = store.upsert_item("u1", conn["id"], "gmail", {"external_id":"m1","item_type":"email","title":"Private","content_summary":"","checksum":"b"*64})
    assert store.get_item("u2", row["id"]) is None
    assert store.list_items("u2") == []


def test_persisted_resource_selection_is_enforced_again_at_sync_boundary():
    store = MemoryIntegrations(); conn = connection(store, "github"); conn["sync_metadata"] = {"selected_resources": ["chronos"]}
    connector = FakeConnector("github", [
        NormalizedIntegrationItem(external_id="1", item_type="github_work", title="Selected", checksum="c"*64, metadata={"repository":"chronos"}),
        NormalizedIntegrationItem(external_id="2", item_type="github_work", title="Unrelated", checksum="d"*64, metadata={"repository":"private-other"}),
    ])
    IntegrationService(repositories(integrations=store), ConnectorRegistry([connector])).sync("u1", "github")
    assert [row["title"] for row in store.items] == ["Selected"]


def test_migration_declares_rls_restricted_grants_and_definer_search_paths():
    sql = (Path(__file__).parents[2] / "supabase" / "migrations" / "027_add_external_integrations.sql").read_text(encoding="utf-8").casefold()
    for table in ("integration_connections", "integration_items", "integration_action_proposals", "integration_audit_events"):
        assert f"alter table public.{table} enable row level security" in sql
    assert "set search_path = pg_catalog" in sql or "set search_path=pg_catalog" in sql
    assert "revoke all on public.integration_connections" in sql
    assert "grant all on public.integration_connections" in sql and "to service_role" in sql
    assert "grant all on public.integration_connections, public.integration_items, public.integration_action_proposals, public.integration_audit_events to authenticated" not in sql
