# Security Model

- Validate bearer tokens through Supabase Auth; never accept user identity from request data.
- Keep RLS enabled and scope every user-owned query by authenticated user ID.
- Keep service-role, Groq, Google client-secret, and encryption credentials on the backend.
- Store Google OAuth token material through Vault-backed functions; never log or return tokens.
- Treat model output and retrieved content as untrusted. Validate structured output with Pydantic before persistence or tool execution.
- Require explicit approval for external writes and bound workflow steps, duration, retries, and request budgets.
- Return stable public errors with request IDs. Keep diagnostic context in redacted structured logs.
- Keep `/demo` static and isolated from user workspaces.

Applied migrations 001–022 are immutable. Migration 017 protects OAuth tokens through Vault; its historical SQL text is retained because changing applied migration history is prohibited.

Core transaction functions are `SECURITY DEFINER` with a restricted `pg_catalog, public` search path. They validate ownership, lock per idempotency key, and revoke execution from `PUBLIC` and `anon`. Only `authenticated` and `service_role` can execute them. RLS remains enabled on operation receipts and every user-owned core table.

`approve_adaptive_plan_transaction` locks the owned pending proposal, validates owned executable commitments and current overlaps, inserts all blocks, changes approval state, writes a concise trace, and records the idempotent result in one transaction. API validation additionally enforces profile hours, protected intervals, transitions, deadlines, and capacity before invoking the RPC.

Google authorization remains read-only. OAuth state is signed and short-lived; access and refresh tokens are retrieved only through service-role Vault RPCs. Status, logs, traces, API responses, and frontend state never contain token material. Groq diagnostics contain provider/model identifiers and classified outcomes, never API keys, raw prompts, raw responses, or hidden reasoning.

MCP is not active. A future MCP adapter must sit behind the same typed tool registry, validate server identity and schemas, minimize scopes, treat retrieved instructions as data, and never let content authorize a tool call.
