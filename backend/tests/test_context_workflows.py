from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.api.dependencies import get_embedding_gateway, get_model_gateway, get_repositories
from app.embeddings.fake import FakeEmbeddingGateway
from app.main import app
from app.models.fake import FakeModelGateway
from app.schemas.adaptive import CandidatePlan, CandidatePlanBlock, PlanningModelOutput
from app.schemas.context import MemoryCreate, MemoryProposal
from app.services.context_service import KnowledgeService, MemoryService
from tests.fakes import MemoryCommitments, MemoryKnowledge, MemoryPlanning, MemoryProjects, repositories

USER = "00000000-0000-0000-0000-000000000001"
client = TestClient(app)


def base_commitment():
    return {"id": "c1", "user_id": USER, "title": "Authentication fix", "description": "Regression suite passes", "type": "hard_deadline", "status": "active", "estimated_minutes": 90, "actual_minutes": 0, "importance": 5, "flexibility": 1, "progress_percent": 0, "risk_score": 65, "risk_level": "at_risk", "confidence_score": .9}


def test_reflection_proposes_but_does_not_confirm_a_working_pattern():
    repos = repositories(commitments=MemoryCommitments([base_commitment()]))
    app.dependency_overrides[get_repositories] = lambda: repos
    response = client.post("/api/v1/reflection", json={"commitment_id": "c1", "planned_minutes": 60, "actual_minutes": 90, "completion_status": "partial", "energy_level": 3, "progress_percent": 40, "notes": "I underestimated authentication debugging twice this week."})
    assert response.status_code == 200
    proposal = response.json()["memory_proposal"]
    assert proposal["category"] == "working_pattern" and proposal["status"] == "proposed"
    assert repos.memory.list_for_user(USER)[0]["status"] == "proposed"


def test_adaptive_planning_cites_retrieved_release_criteria_and_still_requires_approval():
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0); end = start.replace(hour=18)
    candidate = CandidatePlan(label="Protect authentication", summary="One checked block.", blocks=[CandidatePlanBlock(commitment_id="c1", start_at=start + timedelta(hours=1), duration_minutes=60, rationale="Release criteria require stable authentication.")])
    source = {"id": "s1", "user_id": USER, "project_id": None, "title": "Release criteria", "source_type": "note", "status": "ready"}
    chunk = {"id": "k1", "source_id": "s1", "user_id": USER, "project_id": None, "content": "Production readiness requires stable authentication and verified rollback."}
    repos = repositories(commitments=MemoryCommitments([base_commitment()]), knowledge=MemoryKnowledge([source], [chunk]))
    app.dependency_overrides[get_repositories] = lambda: repos
    app.dependency_overrides[get_model_gateway] = lambda: FakeModelGateway(structured=PlanningModelOutput(diagnosis="Authentication is release-critical.", candidates=[candidate]))
    app.dependency_overrides[get_embedding_gateway] = lambda: FakeEmbeddingGateway()
    response = client.post("/api/v1/plan/adaptive", json={"start_at": start.isoformat(), "end_at": end.isoformat()})
    assert response.status_code == 200
    data = response.json()
    assert data["explanation"]["sources"][0]["source_title"] == "Release criteria"
    assert data["requires_approval"] is True and repos.focus.rows == []


def test_adaptive_planning_falls_back_when_retrieval_is_unavailable():
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0); end = start.replace(hour=18)
    candidate = CandidatePlan(label="Protect authentication", summary="One checked block.", blocks=[CandidatePlanBlock(commitment_id="c1", start_at=start + timedelta(hours=1), duration_minutes=60, rationale="Highest deterministic priority.")])
    repos = repositories(commitments=MemoryCommitments([base_commitment()]))
    app.dependency_overrides[get_repositories] = lambda: repos
    app.dependency_overrides[get_model_gateway] = lambda: FakeModelGateway(structured=PlanningModelOutput(diagnosis="Urgent work.", candidates=[candidate]))
    app.dependency_overrides[get_embedding_gateway] = lambda: FakeEmbeddingGateway(fail=RuntimeError("offline"))
    response = client.post("/api/v1/plan/adaptive", json={"start_at": start.isoformat(), "end_at": end.isoformat()})
    assert response.status_code == 200 and response.json()["explanation"]["retrieval_available"] is False


def test_manual_release_context_scenario_is_cited_and_transition_buffer_remains_authoritative():
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0); end = start.replace(hour=18)
    project = {"id": "p1", "user_id": USER, "title": "ChronOS Production Release", "description": "Ship safely", "status": "active", "colour": "accent"}
    planning = MemoryPlanning(events=[{"id": "e1", "user_id": USER, "title": "Team meeting", "start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat(), "status": "busy"}])
    knowledge = MemoryKnowledge(); repos = repositories(commitments=MemoryCommitments([base_commitment() | {"project_id": "p1"}]), projects=MemoryProjects([project]), planning=planning, knowledge=knowledge)
    embedding = FakeEmbeddingGateway()
    note = "Production readiness requires stable authentication, verified rollback, deployment documentation, and a responsive onboarding flow. Calendar write-back is not required for release."
    import asyncio
    asyncio.run(KnowledgeService(repos, embedding).ingest_text(USER, title="Release criteria", source_type="project_context", content=note, project_id="p1", idempotency_key="manual-release-note"))
    MemoryService(repos).create_explicit(USER, MemoryCreate(category="preference", content="I prefer 45-minute focus blocks and do not want important work scheduled immediately after meetings."))
    inferred = MemoryService(repos).propose(USER, MemoryProposal(category="working_pattern", content="I underestimated authentication debugging twice this week.", source_type="reflection", source_reference={"reflection_id": "r1"}, confidence=.65))
    assert inferred and inferred["status"] == "proposed"
    MemoryService(repos).decide(USER, inferred["id"], "confirm")
    invalid = CandidatePlan(label="Too close", summary="Violates transition.", blocks=[CandidatePlanBlock(commitment_id="c1", start_at=start + timedelta(hours=1, minutes=5), duration_minutes=45, rationale="Start immediately.")])
    valid = CandidatePlan(label="Buffered", summary="Respects transition.", blocks=[CandidatePlanBlock(commitment_id="c1", start_at=start + timedelta(hours=1, minutes=10), duration_minutes=45, rationale="Release criteria and prior underestimation justify a protected block.")])
    model = FakeModelGateway(structured=PlanningModelOutput(diagnosis="Authentication is uncertain and release-critical.", candidates=[invalid, valid]))
    app.dependency_overrides[get_repositories] = lambda: repos; app.dependency_overrides[get_model_gateway] = lambda: model; app.dependency_overrides[get_embedding_gateway] = lambda: embedding
    response = client.post("/api/v1/plan/adaptive", json={"start_at": start.isoformat(), "end_at": end.isoformat()})
    assert response.status_code == 200 and response.json()["rejected_candidate_count"] == 1
    sources = response.json()["explanation"]["sources"]
    assert any(source["source_title"] == "Release criteria" for source in sources)
    assert any("45-minute" in source["excerpt"] for source in sources)
    prompt = model.calls[0].prompt
    assert '"estimate_uncertainty_detected":true' in prompt and "Calendar write-back is not required" in prompt
    assert repos.focus.rows == []
