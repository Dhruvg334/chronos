import asyncio

from app.embeddings.fake import FakeEmbeddingGateway
from app.services.context_service import RetrievalService
from tests.fakes import MemoryKnowledge, repositories

USER = "00000000-0000-0000-0000-000000000001"
OTHER = "00000000-0000-0000-0000-000000000002"


def test_hybrid_retrieval_returns_ranked_citations_with_project_and_owner_filters():
    sources = [
        {"id": "s1", "user_id": USER, "project_id": "p1", "title": "Release criteria", "source_type": "project_context", "status": "ready"},
        {"id": "s2", "user_id": OTHER, "project_id": "p1", "title": "Private", "source_type": "note", "status": "ready"},
    ]
    chunks = [
        {"id": "c1", "source_id": "s1", "user_id": USER, "project_id": "p1", "content": "Stable authentication and verified rollback are release criteria."},
        {"id": "c2", "source_id": "s2", "user_id": OTHER, "project_id": "p1", "content": "authentication secret from another user"},
    ]
    citations, available = asyncio.run(RetrievalService(repositories(knowledge=MemoryKnowledge(sources, chunks)), FakeEmbeddingGateway()).retrieve(USER, "authentication rollback", project_id="p1"))
    assert available is True and [item.source_id for item in citations] == ["s1"]
    assert citations[0].retrieval_method == "hybrid" and "Stable authentication" in citations[0].excerpt


def test_retrieval_provider_failure_degrades_without_breaking_planning():
    citations, available = asyncio.run(RetrievalService(repositories(), FakeEmbeddingGateway(fail=RuntimeError("offline"))).retrieve(USER, "release"))
    assert citations == [] and available is False
