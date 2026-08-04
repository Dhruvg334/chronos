# Security Model

- Validate bearer tokens through Supabase Auth; never accept user identity from request data.
- Keep RLS enabled and scope every user-owned query by authenticated user ID.
- Keep service-role, Groq, Google client-secret, and encryption credentials on the backend.
- Store Google OAuth token material through Vault-backed functions; never log or return tokens.
- Treat model output and retrieved content as untrusted. Validate structured output with Pydantic before persistence or tool execution.
- Require explicit approval for external writes and bound workflow steps, duration, retries, and request budgets.
- Return stable public errors with request IDs. Keep diagnostic context in redacted structured logs.
- Keep `/demo` static and isolated from user workspaces.

Applied migrations 001–026 are immutable. Migration 017 protects OAuth tokens through Vault; its historical SQL text is retained because changing applied migration history is prohibited.

Core transaction functions use restricted `SECURITY DEFINER` search paths. Migration 023 narrows `approve_adaptive_plan_transaction` to `pg_catalog` only; every application and authentication object remains explicitly schema-qualified. The functions validate ownership, lock per idempotency key, and revoke execution from `PUBLIC` and `anon`. Only `authenticated` and `service_role` can execute them. RLS remains enabled on operation receipts and every user-owned core table.

`approve_adaptive_plan_transaction` locks the owned pending proposal, validates owned executable commitments and current overlaps, inserts all blocks, changes approval state, writes a concise trace, and records the idempotent result in one transaction. API validation additionally enforces profile hours, protected intervals, transitions, deadlines, and capacity before invoking the RPC.

Migration 024 enables owner-scoped RLS on projects, outcomes, routines, routine occurrences, and weekly plans. Composite ownership foreign keys prevent cross-user links. `approve_weekly_plan_transaction` and the replacement mixed-item intake transaction use a `pg_catalog`-only search path, schema-qualified application/auth objects, ownership checks, idempotency locks, and atomic rollback. Execution is revoked from `PUBLIC` and `anon` and granted only to `authenticated` and `service_role`.

Migration 025 keeps onboarding and personalization on the existing RLS-owned profile and adds immutable owner-scoped recommendation feedback. The API whitelists compact context fields before insertion; raw prompts, raw responses, and hidden reasoning are not accepted into feedback storage. External-action automation remains unavailable.

Migration 026 enables RLS on memory items, knowledge sources, knowledge chunks, and context packs. Composite foreign keys prevent cross-user project and source links. Browser roles can read only their own memory, source metadata, and context-pack metadata; they have no chunk or vector privileges and cannot execute retrieval or ingestion functions. Backend service-role repositories still filter every query by the authenticated user. Atomic ingestion pins the definer search path to `pg_catalog`, validates project ownership and vector dimensions, supports idempotent replay, and rolls back source and chunks together. Hybrid retrieval returns excerpts without embeddings. File content, model prompts, vectors, provider responses, and secrets are excluded from logs.

Google authorization remains read-only. OAuth state is signed and short-lived; access and refresh tokens are retrieved only through service-role Vault RPCs. Status, logs, traces, API responses, and frontend state never contain token material. Groq diagnostics contain provider/model identifiers and classified outcomes, never API keys, raw prompts, raw responses, or hidden reasoning.

MCP is not active. A future MCP adapter must sit behind the same typed tool registry, validate server identity and schemas, minimize scopes, treat retrieved instructions as data, and never let content authorize a tool call.
