# Observability

ChronOS uses a provider-neutral metric sink with no-op local behavior. Sentry, OpenTelemetry, or LLM-tracing adapters must preserve [Operations and recovery](OPERATIONS.md) data minimization. Request and workflow IDs are correlation values; user IDs and raw private content are not metric labels.

HTTP requests receive an `X-Request-ID`. Structured logs record the request ID, path, method, duration, classified event, and redacted diagnostic fields. Workflow traces add workflow IDs, step duration, validation outcome, selected tool, provider/model metadata, and error classification.

Do not use print statements for operations. Do not log authorization headers, API keys, OAuth tokens, raw provider payloads, or sensitive user text. API errors expose public messages and request IDs, not stack traces.

Later work may add OpenTelemetry, Sentry, Langfuse, trace-level evaluations, and prompt/model versioning. None is active today.
