from app.schemas.context import MemoryCreate, MemoryPatch, MemoryProposal
from app.services.context_service import MemoryService
from tests.fakes import MemoryItems, repositories

USER = "00000000-0000-0000-0000-000000000001"
OTHER = "00000000-0000-0000-0000-000000000002"


def test_explicit_memory_is_confirmed_at_full_confidence_and_deduplicated():
    store = MemoryItems(); service = MemoryService(repositories(memory=store))
    created = service.create_explicit(USER, MemoryCreate(category="preference", content="I prefer 45-minute focus blocks."))
    duplicate = service.create_explicit(USER, MemoryCreate(category="preference", content="  I prefer 45-minute focus blocks. "))
    assert created["status"] == "confirmed" and created["is_explicit"] is True and created["confidence"] == 1
    assert duplicate["id"] == created["id"] and duplicate["duplicate"] is True and len(store.rows) == 1


def test_inferred_memory_requires_confirmation_and_sensitive_content_is_not_inferred():
    service = MemoryService(repositories())
    proposed = service.propose(USER, MemoryProposal(category="working_pattern", content="I underestimated authentication debugging twice.", source_type="reflection", source_reference={"reflection_id": "r1"}, confidence=.65))
    assert proposed and proposed["status"] == "proposed" and proposed["is_explicit"] is False
    assert service.decide(USER, proposed["id"], "confirm")["status"] == "confirmed"
    assert service.propose(USER, MemoryProposal(category="working_pattern", content="A medical diagnosis affects my work.", source_type="reflection", confidence=.7)) is None


def test_corrections_preserve_history_and_contradictions_are_surfaced_not_overwritten():
    service = MemoryService(repositories())
    first = service.create_explicit(USER, MemoryCreate(category="personal_rule", content="Do not schedule important work immediately after meetings."))
    service.create_explicit(USER, MemoryCreate(category="personal_rule", content="Schedule important work immediately after meetings."))
    listed = service.list(USER, "personal_rule")
    assert any(item["conflicts"] for item in listed)
    corrected = service.update(USER, first["id"], MemoryPatch(content="Do not schedule deep work immediately after meetings."))
    assert corrected["source_reference"]["correction_history"][0]["content"].startswith("Do not schedule important")


def test_memory_repository_never_returns_another_users_items():
    store = MemoryItems([{"id": "a", "user_id": USER, "category": "preference", "content": "Alpha"}, {"id": "b", "user_id": OTHER, "category": "preference", "content": "Beta"}])
    assert [item["id"] for item in store.list_for_user(USER)] == ["a"]
    assert store.get_for_user(USER, "b") is None
