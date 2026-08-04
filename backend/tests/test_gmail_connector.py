from app.integrations.adapters import GmailConnector
from app.integrations.registry import ConnectorRegistry
from app.integrations.service import IntegrationService
from tests.fakes import MemoryIntegrations, repositories


def test_gmail_reduces_quotes_and_creates_reviewable_deadline_dependency_proposal():
    connector = GmailConnector(is_configured=True); connector.set_fixture_rows([{"id":"m1","subject":"Auth regression deadline","body":"Please finish before 3 PM tomorrow. Deployment cannot proceed until session tests pass. Do not change the production calendar.\nOn Monday someone wrote:\nold reply","thread_id":"t1"}])
    store = MemoryIntegrations(); store.create_connection("u", {"id":"c","provider":"gmail","status":"connected","sync_cursor":None,"sync_metadata":{}})
    IntegrationService(repositories(integrations=store), ConnectorRegistry([connector])).sync("u", "gmail")
    assert "old reply" not in store.items[0]["content_summary"]
    assert store.items[0]["metadata"]["untrusted_content"] is True
    proposal = store.proposals[0]
    assert proposal["status"] == "pending"
    assert proposal["validated_payload"]["signals"] == ["deadline", "dependency"]
    assert "production calendar" in proposal["validated_payload"]["source_excerpt"]
