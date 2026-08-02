# Security Model

- Validate bearer tokens through Supabase Auth; never accept user identity from request data.
- Keep RLS enabled and scope every user-owned query by authenticated user ID.
- Keep service-role, Groq, Google client-secret, and encryption credentials on the backend.
- Store Google OAuth token material through Vault-backed functions; never log or return tokens.
- Treat model output and retrieved content as untrusted. Validate structured output with Pydantic before persistence or tool execution.
- Require explicit approval for external writes and bound workflow steps, duration, retries, and request budgets.
- Return stable public errors with request IDs. Keep diagnostic context in redacted structured logs.
- Keep `/demo` static and isolated from user workspaces.

Applied migrations 001–018 are immutable. Migration 017 protects OAuth tokens through Vault; its historical SQL text is retained because changing applied migration history is prohibited.

MCP is not active. A future MCP adapter must sit behind the same typed tool registry, validate server identity and schemas, minimize scopes, treat retrieved instructions as data, and never let content authorize a tool call.
