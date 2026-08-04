from __future__ import annotations

import hashlib
import io
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.errors import ChronosError, ErrorCode
from app.embeddings.gateway import EmbeddingGateway
from app.repositories.protocols import RepositorySet
from app.schemas.context import Citation, ContextPackView, MemoryCreate, MemoryPatch, MemoryProposal

_SPACE = re.compile(r"\s+")
_SENSITIVE_INFERENCE = re.compile(r"\b(password|secret|diagnos|medical|religion|sexual|bank|credit card|trauma)\b", re.I)
_INFERENCE_SIGNALS = re.compile(r"\b(prefer|work best|underestimat|twice|repeated|always|usually|blocked by)\b", re.I)


def normalize_text(value: str) -> str:
    return _SPACE.sub(" ", value.replace("\x00", " ")).strip()


def fingerprint(category: str, content: str, project_id: str | None) -> str:
    normalized = f"{category}|{project_id or ''}|{normalize_text(content).casefold()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def token_estimate(value: str) -> int:
    return max(1, round(len(value.split()) * 1.3))


class MemoryService:
    def __init__(self, repositories: RepositorySet):
        self.repositories = repositories

    def _assert_project(self, user_id: str, project_id: str | None) -> None:
        if project_id and not self.repositories.projects.get_for_user(user_id, project_id):
            raise ChronosError(ErrorCode.VALIDATION, "Project not found.")

    def list(self, user_id: str, category: str | None = None, project_id: str | None = None) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        rows = self.repositories.memory.list_for_user(user_id, category, project_id)
        for row in rows:
            expiry = row.get("expires_at")
            if row.get("status") in {"proposed", "confirmed"} and expiry and datetime.fromisoformat(str(expiry).replace("Z", "+00:00")) <= now:
                row = self.repositories.memory.update(user_id, str(row["id"]), {"status": "expired"})
            row["conflicts"] = self._conflicts(row, rows)
        priority = {"confirmed": 0, "proposed": 1, "expired": 2, "archived": 3, "rejected": 4}
        return sorted(rows, key=lambda row: (priority.get(row.get("status"), 9), not bool(row.get("is_explicit")), str(row.get("updated_at", ""))), reverse=False)

    @staticmethod
    def _conflicts(item: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, str]]:
        if item.get("status") not in {"proposed", "confirmed"}: return []
        words = set(normalize_text(str(item.get("content", ""))).casefold().split())
        polarity = "negative" if re.search(r"\b(not|never|avoid|don't|do not)\b", str(item.get("content", "")), re.I) else "positive"
        conflicts = []
        for other in rows:
            if other is item or other.get("id") == item.get("id") or other.get("category") != item.get("category") or other.get("status") not in {"proposed", "confirmed"}: continue
            other_words = set(normalize_text(str(other.get("content", ""))).casefold().split())
            overlap = len(words & other_words) / max(1, len(words | other_words))
            other_polarity = "negative" if re.search(r"\b(not|never|avoid|don't|do not)\b", str(other.get("content", "")), re.I) else "positive"
            if overlap >= 0.35 and polarity != other_polarity:
                conflicts.append({"id": str(other["id"]), "content": str(other["content"]), "message": "This may conflict with another active memory."})
        return conflicts

    def create_explicit(self, user_id: str, request: MemoryCreate) -> dict[str, Any]:
        self._assert_project(user_id, request.project_id)
        content = normalize_text(request.content)
        content_hash = fingerprint(request.category, content, request.project_id)
        existing = next((row for row in self.repositories.memory.list_for_user(user_id, request.category, request.project_id)
                         if row.get("content_fingerprint") == content_hash and row.get("status") in {"confirmed", "proposed"}), None)
        if existing: return {**existing, "duplicate": True}
        return self.repositories.memory.create(user_id, {
            "id": str(uuid.uuid4()), **request.model_dump(mode="json"), "content": content,
            "source_type": "user", "source_reference": {"label": "Added by you"},
            "confidence": 1.0, "is_explicit": True, "status": "confirmed", "content_fingerprint": content_hash,
        })

    def propose(self, user_id: str, request: MemoryProposal) -> dict[str, Any] | None:
        self._assert_project(user_id, request.project_id)
        content = normalize_text(request.content)
        if _SENSITIVE_INFERENCE.search(content): return None
        content_hash = fingerprint(request.category, content, request.project_id)
        existing = next((row for row in self.repositories.memory.list_for_user(user_id, request.category, request.project_id)
                         if row.get("content_fingerprint") == content_hash and row.get("status") in {"confirmed", "proposed"}), None)
        if existing: return {**existing, "duplicate": True}
        return self.repositories.memory.create(user_id, {
            "id": str(uuid.uuid4()), **request.model_dump(mode="json"), "content": content,
            "is_explicit": False, "status": "proposed", "content_fingerprint": content_hash,
        })

    def update(self, user_id: str, memory_id: str, patch: MemoryPatch) -> dict[str, Any]:
        current = self.repositories.memory.get_for_user(user_id, memory_id)
        if not current: raise ChronosError(ErrorCode.VALIDATION, "Memory not found.")
        changes = patch.model_dump(mode="json", exclude_unset=True)
        self._assert_project(user_id, changes.get("project_id", current.get("project_id")))
        content = normalize_text(changes.get("content", current["content"]))
        category = changes.get("category", current["category"])
        project_id = changes.get("project_id", current.get("project_id"))
        reference = dict(current.get("source_reference") or {})
        if content != current["content"]:
            history = list(reference.get("correction_history") or [])[-9:]
            history.append({"content": current["content"], "corrected_at": datetime.now(timezone.utc).isoformat()})
            reference["correction_history"] = history
        changes.update(content=content, content_fingerprint=fingerprint(category, content, project_id), source_reference=reference)
        return self.repositories.memory.update(user_id, memory_id, changes)

    def decide(self, user_id: str, memory_id: str, decision: str) -> dict[str, Any]:
        current = self.repositories.memory.get_for_user(user_id, memory_id)
        if not current: raise ChronosError(ErrorCode.VALIDATION, "Memory not found.")
        target = {"confirm": "confirmed", "reject": "rejected", "archive": "archived", "expire": "expired"}[decision]
        return self.repositories.memory.update(user_id, memory_id, {"status": target})

    def propose_from_reflection(self, user_id: str, reflection: dict[str, Any]) -> dict[str, Any] | None:
        notes = normalize_text(str(reflection.get("notes") or reflection.get("blocker_reason") or ""))
        if not notes or not _INFERENCE_SIGNALS.search(notes) or _SENSITIVE_INFERENCE.search(notes): return None
        category = "working_pattern" if re.search(r"underestimat|twice|repeated|usually", notes, re.I) else "preference"
        return self.propose(user_id, MemoryProposal(
            category=category, content=notes, source_type="reflection", confidence=0.65,
            source_reference={"reflection_id": str(reflection["id"]), "label": "Proposed from a reflection"},
        ))


class KnowledgeService:
    ALLOWED_SUFFIXES = {".txt": "text/plain", ".md": "text/markdown", ".pdf": "application/pdf"}

    def __init__(self, repositories: RepositorySet, embeddings: EmbeddingGateway):
        self.repositories = repositories
        self.embeddings = embeddings

    @staticmethod
    def _chunks(text: str, size: int = 1200, overlap: int = 160) -> list[str]:
        paragraphs = [normalize_text(part) for part in re.split(r"\n\s*\n", text) if normalize_text(part)]
        chunks: list[str] = []
        current = ""
        for paragraph in paragraphs:
            if len(current) + len(paragraph) + 1 <= size:
                current = f"{current}\n{paragraph}".strip()
            else:
                if current: chunks.append(current)
                current = f"{current[-overlap:]} {paragraph}".strip() if current else paragraph
                while len(current) > size:
                    chunks.append(current[:size])
                    current = current[size-overlap:]
        if current: chunks.append(current)
        return chunks[:200]

    async def ingest_text(self, user_id: str, *, title: str, source_type: str, content: str, project_id: str | None, idempotency_key: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        if project_id and not self.repositories.projects.get_for_user(user_id, project_id):
            raise ChronosError(ErrorCode.VALIDATION, "Project not found.")
        normalized = normalize_text(content)
        if not normalized: raise ChronosError(ErrorCode.VALIDATION, "The source did not contain readable text.")
        if len(normalized.encode("utf-8")) > settings.KNOWLEDGE_MAX_FILE_BYTES:
            raise ChronosError(ErrorCode.VALIDATION, "This source is larger than the allowed limit.")
        checksum = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        pieces = self._chunks(content)
        try:
            embedded = await self.embeddings.embed(pieces)
        except ChronosError:
            self._record_failed(user_id, title, source_type, project_id, checksum, metadata, "embedding_unavailable")
            raise
        if embedded.dimensions != settings.EMBEDDING_DIMENSIONS or len(embedded.vectors) != len(pieces):
            self._record_failed(user_id, title, source_type, project_id, checksum, metadata, "embedding_dimension")
            raise ChronosError(ErrorCode.MODEL_OUTPUT_INVALID, "The source could not be indexed safely.")
        source_id = str(uuid.uuid4())
        source = {"id": source_id, "project_id": project_id, "source_type": source_type, "title": title,
                  "checksum": checksum, "original_metadata": {**(metadata or {}), "untrusted_content": True,
                  "embedding_provider": embedded.provider, "embedding_model": embedded.model}}
        chunks = [{"id": str(uuid.uuid4()), "content": piece, "embedding": vector,
                   "token_count": token_estimate(piece), "position": index,
                   "metadata": {"untrusted_content": True}} for index, (piece, vector) in enumerate(zip(pieces, embedded.vectors))]
        return self.repositories.knowledge.ingest(user_id, idempotency_key, source, chunks)

    def _record_failed(self, user_id: str, title: str, source_type: str, project_id: str | None, checksum: str, metadata: dict[str, Any] | None, code: str) -> None:
        try:
            self.repositories.knowledge.create_failed_source(user_id, {"id": str(uuid.uuid4()), "project_id": project_id,
                "source_type": source_type, "title": title, "checksum": checksum,
                "original_metadata": {**(metadata or {}), "untrusted_content": True}, "failure_code": code})
        except Exception:
            pass

    async def ingest_file(self, user_id: str, *, filename: str, content_type: str | None, data: bytes, project_id: str | None, idempotency_key: str) -> dict[str, Any]:
        suffix = Path(filename).suffix.casefold()
        if suffix not in self.ALLOWED_SUFFIXES or (content_type and content_type not in {self.ALLOWED_SUFFIXES[suffix], "application/octet-stream"}):
            raise ChronosError(ErrorCode.VALIDATION, "Use a plain-text, Markdown, or PDF file.")
        if not data or len(data) > settings.KNOWLEDGE_MAX_FILE_BYTES:
            raise ChronosError(ErrorCode.VALIDATION, "The file is empty or larger than the allowed limit.")
        checksum = hashlib.sha256(data).hexdigest()
        try:
            if suffix == ".pdf":
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(data))
                text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
            else:
                text = data.decode("utf-8")
        except Exception as exc:
            self._record_failed(user_id, Path(filename).name, "document", project_id, checksum,
                                {"filename": Path(filename).name, "content_type": self.ALLOWED_SUFFIXES[suffix]}, "extraction_failed")
            raise ChronosError(ErrorCode.VALIDATION, "The file text could not be read safely.") from exc
        return await self.ingest_text(user_id, title=Path(filename).name, source_type="document", content=text,
                                      project_id=project_id, idempotency_key=idempotency_key,
                                      metadata={"filename": Path(filename).name, "content_type": self.ALLOWED_SUFFIXES[suffix], "size_bytes": len(data)})


class RetrievalService:
    def __init__(self, repositories: RepositorySet, embeddings: EmbeddingGateway):
        self.repositories = repositories; self.embeddings = embeddings

    async def retrieve(self, user_id: str, query: str, *, project_id: str | None = None, limit: int = 6) -> tuple[list[Citation], bool]:
        try:
            result = await self.embeddings.embed([normalize_text(query)])
            if result.dimensions != settings.EMBEDDING_DIMENSIONS: raise ValueError("dimension mismatch")
            rows = self.repositories.knowledge.retrieve(user_id, query, result.vectors[0], project_id, limit)
        except Exception:
            return [], False
        citations = [Citation(source_id=str(row["source_id"]), source_title=row["title"], source_type=row["source_type"],
            excerpt=row["excerpt"], score=float(row.get("score") or 0), retrieval_method="hybrid",
            confidence="high" if float(row.get("score") or 0) >= .03 else "medium" if float(row.get("score") or 0) > 0 else "low",
            reason_selected="Matched the planning question using document meaning and exact terms.") for row in rows]
        return citations, True


class ContextPackService:
    def __init__(self, repositories: RepositorySet, embeddings: EmbeddingGateway):
        self.repositories = repositories; self.retrieval = RetrievalService(repositories, embeddings)

    async def build(self, user_id: str, *, purpose: str, project_id: str | None = None,
                    commitment_id: str | None = None, outcome_id: str | None = None,
                    query: str | None = None, token_budget: int | None = None) -> ContextPackView:
        budget = token_budget or settings.CONTEXT_PACK_TOKEN_BUDGET
        project = self.repositories.projects.get_for_user(user_id, project_id) if project_id else None
        if project_id and not project: raise ChronosError(ErrorCode.VALIDATION, "Project not found.")
        outcome = self.repositories.outcomes.get_for_user(user_id, outcome_id) if outcome_id else None
        commitment = self.repositories.commitments.get_for_user(user_id, commitment_id) if commitment_id else None
        memories = [row for row in MemoryService(self.repositories).list(user_id)
                    if row.get("status") == "confirmed"
                    and (not row.get("project_id") or str(row.get("project_id")) == str(project_id))]
        memories.sort(key=lambda row: (not bool(row.get("is_explicit")), -float(row.get("confidence") or 0), str(row.get("updated_at", ""))))
        search_query = query or " ".join(filter(None, [project.get("title") if project else None,
            outcome.get("completion_criteria") if outcome else None, commitment.get("title") if commitment else None, purpose.replace("_", " ")]))
        citations, available = await self.retrieval.retrieve(user_id, search_query or purpose, project_id=project_id, limit=6)
        lines: list[str] = []
        provenance: list[dict[str, Any]] = []
        pack_citations: list[Citation] = []
        for label, row in (("Project", project), ("Outcome", outcome), ("Commitment", commitment)):
            if row:
                content = row.get("completion_criteria") or row.get("description") or row.get("title")
                lines.append(f"{label}: {row.get('title')}. {content}")
                provenance.append({"type": "structured", "label": label, "entity_id": str(row["id"])})
                pack_citations.append(Citation(source_id=str(row["id"]), source_title=f"{label}: {row.get('title')}",
                    source_type=label.casefold(), excerpt=str(content)[:600], reason_selected=f"Current {label.casefold()} context.",
                    confidence="high", retrieval_method="structured", score=1))
        for memory in memories:
            line = f"Confirmed {memory['category'].replace('_',' ')}: {memory['content']}"
            if token_estimate("\n".join([*lines, line])) > budget: break
            lines.append(line); provenance.append({"type": "memory", "memory_id": str(memory["id"]), "label": memory.get("source_reference", {}).get("label", "Confirmed memory")})
            pack_citations.append(Citation(source_id=str(memory["id"]),
                source_title=memory.get("source_reference", {}).get("label", f"Confirmed {memory['category'].replace('_',' ')}"),
                source_type=f"memory:{memory['category']}", excerpt=str(memory["content"])[:600],
                reason_selected="A confirmed preference, constraint, or pattern relevant to this context.",
                confidence="high" if memory.get("is_explicit") else "medium", retrieval_method="memory", score=float(memory.get("confidence") or 0)))
        seen_sources: set[str] = set()
        for citation in citations:
            if citation.source_id in seen_sources: continue
            line = f"Source {citation.source_title}: {citation.excerpt}"
            if token_estimate("\n".join([*lines, line])) > budget: break
            lines.append(line); pack_citations.append(citation); seen_sources.add(citation.source_id)
            provenance.append({"type": "knowledge", "source_id": citation.source_id, "title": citation.source_title, "excerpt": citation.excerpt})
        summary = "\n".join(lines)[:12000]
        contradictions = [{"memory_id": str(row["id"]), "conflicts": row.get("conflicts", [])} for row in memories if row.get("conflicts")]
        expires_at = datetime.now(timezone.utc) + timedelta(hours=2 if purpose in {"daily_planning", "recovery", "stuck"} else 24)
        stored = self.repositories.context_packs.create(user_id, {"id": str(uuid.uuid4()), "purpose": purpose,
            "entity_references": {"project_id": project_id, "outcome_id": outcome_id, "commitment_id": commitment_id},
            "source_references": [citation.model_dump() for citation in pack_citations], "generated_summary": summary,
            "provenance": provenance, "token_count": token_estimate(summary) if summary else 0, "expires_at": expires_at.isoformat()})
        return ContextPackView(id=str(stored["id"]), purpose=purpose, summary=summary,
            token_count=int(stored.get("token_count") or token_estimate(summary) if summary else 0), citations=pack_citations,
            contradictions=contradictions, expires_at=stored.get("expires_at", expires_at), retrieval_available=available)
