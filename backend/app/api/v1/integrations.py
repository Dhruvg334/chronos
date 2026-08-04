from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import get_connector_registry, get_current_user, get_embedding_gateway, get_repositories
from app.core.observability import request_id_context
from app.embeddings.gateway import EmbeddingGateway
from app.integrations.obsidian import ObsidianImportAdapter
from app.integrations.registry import ConnectorRegistry
from app.integrations.service import IntegrationService
from app.repositories.protocols import RepositorySet
from app.schemas.integrations import IntegrationProposalRequest, ProposalApprovalRequest, ProposalDecisionRequest, ResourceSelectionRequest
from app.services.context_service import KnowledgeService
from app.services.usage_limits import UsageCategory, enforce_if_available

router = APIRouter()


@router.get("")
def catalog(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories), registry: ConnectorRegistry = Depends(get_connector_registry)):
    return {"integrations": IntegrationService(repositories, registry).catalog(user_id)}


@router.get("/items")
def list_items(provider: str | None = None, project_id: str | None = None, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return {"items": repositories.integrations.list_items(user_id, provider, project_id, 100)}


@router.post("/{provider}/sync")
def sync(provider: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories), registry: ConnectorRegistry = Depends(get_connector_registry)):
    enforce_if_available(repositories.operations, user_id, UsageCategory.INTEGRATION_SYNC)
    return IntegrationService(repositories, registry).sync(user_id, provider, request_id=request_id_context.get())


@router.post("/{provider}/disconnect")
def disconnect(provider: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories), registry: ConnectorRegistry = Depends(get_connector_registry)):
    IntegrationService(repositories, registry).disconnect(user_id, provider, request_id=request_id_context.get())
    return {"status": "revoked"}


@router.put("/{provider}/resources")
def select_resources(provider: str, request: ResourceSelectionRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories), registry: ConnectorRegistry = Depends(get_connector_registry)):
    registry.get(provider)
    connection = repositories.integrations.get_connection(user_id, provider)
    if not connection:
        from app.core.errors import ChronosError, ErrorCode
        raise ChronosError(ErrorCode.VALIDATION, "Connect this provider before selecting resources.")
    resources = list(dict.fromkeys(value.strip() for value in request.resources if value.strip()))
    metadata = {**(connection.get("sync_metadata") or {}), "selected_resources": resources[:50]}
    repositories.integrations.update_connection(user_id, connection["id"], {"sync_metadata": metadata, "sync_cursor": None})
    repositories.integrations.append_audit(user_id, {"connection_id": connection["id"], "provider": provider, "event_type": "resource_selection", "outcome": "updated", "safe_metadata": {"item_count": len(resources)}})
    return {"provider": provider, "selected_resources": resources[:50]}


@router.get("/proposals/pending")
def pending(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    proposals = repositories.integrations.list_proposals(user_id)
    result = []
    for proposal in proposals:
        item = repositories.integrations.get_item(user_id, proposal.get("integration_item_id"))
        result.append({**proposal, "provider": item.get("provider") if item else None, "source_excerpt": (item.get("content_summary") or "")[:600] if item else "", "source_url": item.get("source_url") if item else None})
    return {"proposals": result}


@router.post("/proposals")
def propose(request: IntegrationProposalRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories), registry: ConnectorRegistry = Depends(get_connector_registry)):
    enforce_if_available(repositories.operations, user_id, UsageCategory.PROPOSAL)
    item = repositories.integrations.get_item(user_id, request.item_id)
    if not item: from app.core.errors import ChronosError, ErrorCode; raise ChronosError(ErrorCode.VALIDATION, "External source was not found.")
    payload = {"project_id": request.project_id, "source_item_id": request.item_id, "untrusted_content": True}
    return IntegrationService(repositories, registry).propose(user_id, item["connection_id"], request.item_id, request.action_type, request.safe_summary, payload, request.idempotency_key)


@router.post("/proposals/{proposal_id}/decision")
def decide(proposal_id: str, request: ProposalDecisionRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    proposals = repositories.integrations.list_proposals(user_id)
    proposal = next((row for row in proposals if str(row["id"]) == str(proposal_id)), None)
    updated = repositories.integrations.update_proposal(user_id, proposal_id, {"status": request.decision, "resolved_at": datetime.now(timezone.utc).isoformat()})
    item = repositories.integrations.get_item(user_id, proposal.get("integration_item_id")) if proposal else None
    repositories.integrations.append_audit(user_id, {"connection_id": proposal.get("connection_id") if proposal else None, "provider": item.get("provider") if item else "unknown", "event_type": "rejection", "outcome": request.decision, "safe_metadata": {"action_type": proposal.get("action_type") if proposal else "unknown"}})
    return updated


@router.post("/proposals/{proposal_id}/approve")
def approve(proposal_id: str, request: ProposalApprovalRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return repositories.integrations.approve_proposal(user_id, proposal_id, request.action_type, request.project_id)


@router.post("/obsidian/import")
async def import_obsidian(file: UploadFile = File(...), project_id: str | None = Form(default=None), user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories), embeddings: EmbeddingGateway = Depends(get_embedding_gateway)):
    data = await file.read(); notes = ObsidianImportAdapter().read(file.filename or "notes.md", data); service = KnowledgeService(repositories, embeddings)
    enforce_if_available(repositories.operations, user_id, UsageCategory.INGESTION)
    enforce_if_available(repositories.operations, user_id, UsageCategory.INGESTION_BYTES, len(data))
    enforce_if_available(repositories.operations, user_id, UsageCategory.EMBEDDING)
    results = []
    for note in notes:
        result = await service.ingest_text(user_id, title=note.title, source_type="project_context" if project_id else "document", content=note.text, project_id=project_id, idempotency_key=f"obsidian:{project_id or 'general'}:{note.relative_path}", metadata={"relative_path": note.relative_path, "links": list(note.links), "provider": "obsidian", "untrusted_content": True})
        results.append(result)
    return {"imported": sum(1 for row in results if row.get("status") == "ready"), "duplicates": sum(1 for row in results if row.get("status") == "duplicate"), "sources": results}
