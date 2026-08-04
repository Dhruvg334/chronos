import asyncio
from datetime import datetime, timezone

from app.embeddings.fake import FakeEmbeddingGateway
from app.services.context_service import ContextPackService
from tests.fakes import MemoryCommitments, MemoryContextPacks, MemoryItems, MemoryKnowledge, MemoryProjects, repositories

USER = "00000000-0000-0000-0000-000000000001"


def test_context_pack_orders_structured_memory_and_sources_within_budget():
    project = {"id": "p1", "user_id": USER, "title": "ChronOS Production Release", "description": "Ship a stable release"}
    memory = {"id": "m1", "user_id": USER, "category": "preference", "content": "I prefer 45-minute focus blocks.", "status": "confirmed", "is_explicit": True, "confidence": 1, "source_reference": {"label": "Confirmed preference"}, "updated_at": datetime.now(timezone.utc).isoformat()}
    source = {"id": "s1", "user_id": USER, "project_id": "p1", "title": "Release criteria", "source_type": "project_context", "status": "ready"}
    chunk = {"id": "c1", "source_id": "s1", "user_id": USER, "project_id": "p1", "content": "Stable authentication, verified rollback, deployment documentation, and responsive onboarding."}
    packs = MemoryContextPacks()
    pack = asyncio.run(ContextPackService(repositories(projects=MemoryProjects([project]), memory=MemoryItems([memory]), knowledge=MemoryKnowledge([source], [chunk]), context_packs=packs), FakeEmbeddingGateway()).build(USER, purpose="project_planning", project_id="p1", query="release criteria authentication", token_budget=300))
    assert pack.token_count <= 300 and any(citation.source_id == "s1" for citation in pack.citations)
    assert pack.summary.startswith("Project:") and "Confirmed preference" in pack.summary
    assert packs.rows[0]["provenance"][0]["type"] == "structured"


def test_context_pack_survives_missing_retrieval_with_structured_context():
    commitments = MemoryCommitments([{"id": "c1", "user_id": USER, "title": "Authentication fix", "description": "Run regression suite"}])
    pack = asyncio.run(ContextPackService(repositories(commitments=commitments), FakeEmbeddingGateway(fail=RuntimeError("offline"))).build(USER, purpose="recovery", commitment_id="c1", token_budget=300))
    assert pack.retrieval_available is False and "Authentication fix" in pack.summary
    assert len(pack.citations) == 1 and pack.citations[0].retrieval_method == "structured"
