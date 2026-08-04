from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.api.dependencies import get_current_user, get_embedding_gateway, get_repositories
from app.embeddings.gateway import EmbeddingGateway
from app.repositories.protocols import RepositorySet
from app.schemas.context import ContextPackRequest, KnowledgeTextCreate, MemoryCreate, MemoryDecision, MemoryPatch, RetrievalRequest
from app.services.context_service import ContextPackService, KnowledgeService, MemoryService, RetrievalService

router = APIRouter()


@router.get("/memory")
async def list_memory(category: str | None = Query(default=None), project_id: str | None = Query(default=None),
                      user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return {"items": MemoryService(repositories).list(user_id, category, project_id)}


@router.post("/memory", status_code=status.HTTP_201_CREATED)
async def create_memory(request: MemoryCreate, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return MemoryService(repositories).create_explicit(user_id, request)


@router.put("/memory/{memory_id}")
async def update_memory(memory_id: str, request: MemoryPatch, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return MemoryService(repositories).update(user_id, memory_id, request)


@router.post("/memory/{memory_id}/decision")
async def decide_memory(memory_id: str, request: MemoryDecision, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return MemoryService(repositories).decide(user_id, memory_id, request.decision)


@router.get("/memory-export")
async def export_memory(user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return {"exported_at": datetime.now(timezone.utc).isoformat(), "items": MemoryService(repositories).list(user_id)}


@router.get("/knowledge")
async def list_knowledge(project_id: str | None = Query(default=None), user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return {"sources": repositories.knowledge.list_sources(user_id, project_id)}


@router.post("/knowledge/text", status_code=status.HTTP_201_CREATED)
async def ingest_text(request: KnowledgeTextCreate, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories), embeddings: EmbeddingGateway = Depends(get_embedding_gateway)):
    return await KnowledgeService(repositories, embeddings).ingest_text(user_id, **request.model_dump())


@router.post("/knowledge/file", status_code=status.HTTP_201_CREATED)
async def ingest_file(file: UploadFile = File(...), project_id: str | None = Form(default=None), idempotency_key: str = Form(..., min_length=8, max_length=160),
                      user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories), embeddings: EmbeddingGateway = Depends(get_embedding_gateway)):
    data = await file.read()
    return await KnowledgeService(repositories, embeddings).ingest_file(user_id, filename=file.filename or "document", content_type=file.content_type,
                                                                        data=data, project_id=project_id, idempotency_key=idempotency_key)


@router.post("/knowledge/{source_id}/archive")
async def archive_source(source_id: str, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories)):
    return repositories.knowledge.update_source(user_id, source_id, {"status": "archived"})


@router.post("/retrieve")
async def retrieve(request: RetrievalRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories), embeddings: EmbeddingGateway = Depends(get_embedding_gateway)):
    citations, available = await RetrievalService(repositories, embeddings).retrieve(user_id, request.query, project_id=request.project_id, limit=request.limit)
    return {"results": [citation.model_dump() for citation in citations], "retrieval_available": available}


@router.post("/packs")
async def create_context_pack(request: ContextPackRequest, user_id: str = Depends(get_current_user), repositories: RepositorySet = Depends(get_repositories), embeddings: EmbeddingGateway = Depends(get_embedding_gateway)):
    return await ContextPackService(repositories, embeddings).build(user_id, **request.model_dump())
