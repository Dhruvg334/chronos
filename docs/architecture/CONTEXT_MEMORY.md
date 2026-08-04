# Context, Memory, and Retrieval

ChronOS keeps attributable context in four owner-scoped structures introduced by migration 026. `memory_items` stores explicit and proposed memories with category, confidence, confirmation state, dates, and source reference. `knowledge_sources` records notes, pasted text, project context, and documents. `knowledge_chunks` contains deterministic chunks plus backend-only 384-dimensional vectors and lexical indexes. `context_packs` records bounded, expiring context with entity references, citations, and provenance.

The legacy `user_memory` key/value table from migration 013 remains unchanged for compatibility. New context features do not read or rewrite it.

## Memory rules

Explicit statements are confirmed at confidence 1.0. Inferred observations remain proposed until confirmation and are never generated for sensitive free-form content. Active duplicate fingerprints are rejected. Contradictory active memories are shown together for review rather than overwritten. Corrections preserve the previous wording in source history. Confirmed explicit memory sorts ahead of inferred memory; expired, rejected, and archived items do not enter context packs.

## Ingestion

Text, Markdown, pasted notes, project context, and text-bearing PDFs are accepted up to the configured byte limit. PDF extraction uses `pypdf`; OCR is not performed. Normalized text receives a SHA-256 checksum, deterministic overlapping chunks, bounded token estimates, batch embeddings, dimension validation, and one atomic source-plus-chunks transaction. Duplicate checksums return the existing source. Extraction or embedding failure produces a safe failed state without partial chunks. Document text is marked untrusted and is never executed as workflow instruction.

## Embeddings and retrieval

`EmbeddingGateway` is provider-neutral. `local_hash` is the offline, privacy-preserving fallback and supports deterministic tests; it is not presented as semantic production quality. The optional `huggingface` adapter uses the configurable `sentence-transformers/all-MiniLM-L6-v2` model, bounded batches, timeout, retry, rate-limit classification, and 384-dimension validation. Provider secrets and document bodies are not logged.

Hybrid retrieval runs in PostgreSQL with dense cosine rank, lexical rank, deterministic reciprocal-rank fusion, project filtering, owner filtering, and a small source-type weight. It returns excerpts and citation metadata, never vectors. Planning continues from repositories and deterministic capacity rules when embeddings or retrieval are unavailable.

## Context packs and provenance

Daily, weekly, project, recovery, stuck, and reflection packs order structured entities first, then confirmed explicit/inferred memory, then deduplicated retrieved excerpts. Each pack has a token budget and short expiration. Summaries are deterministic source compilations rather than hidden model reasoning. Adaptive planning and recovery may include these packs, but all candidate plans, permissions, overlap, availability, capacity, dependency, and approval checks remain authoritative.

The UI places memory and knowledge inside Settings. Users can inspect sources and correction history, confirm or reject proposals, resolve conflicts, archive items, export memory, and inspect exact excerpts that materially affected plan explanations.
