# Operations and recovery

## Failure and version contract

`app.core.failures.FailureCode` is the shared operational classification for APIs, traces, logs, audit events, and evaluations. Public API errors preserve the stable product error code and add a safe failure code and correlation request ID. Stack traces and provider payloads are never public.

Model requests carry explicit prompt and schema versions. Responses record provider, model, latency, request count, bounded repair count, and token usage when supplied. ChronOS does not store raw prompts by default.

## Telemetry and health

The default metric sink is a no-op. Provider-neutral counters and timings cover HTTP, model, retrieval, database, synchronization, approvals, and rollbacks. Sentry, OpenTelemetry, and LLM-tracing adapters belong at this boundary and must use the redaction policy. Raw messages, documents, tokens, credentials, hidden reasoning, and unrestricted personal content are prohibited.

Liveness is dependency-free. Public readiness performs a short, cached database/schema check and returns safe component states without expensive model calls. Authenticated operational status adds model and embedding configuration, migration compatibility, integration configuration, and bounded inline-processing state without identifiers or internal URLs. States are `ready`, `degraded`, and `not_ready`.

## Limits and retries

Hourly user/global budgets cover model calls, embeddings, ingestion requests and bytes, integration sync, MCP calls, proposals, and failed approvals. Atomic Postgres enforcement occurs before provider calls. Denials include retry information and an audit event. Workflow request budgets remain a per-run bound.

Provider retries are bounded and use deterministic exponential backoff for retryable network and server failures. Transactions and normalized sync use idempotency keys. Failed ingestion/provider states support manual retry without repeating successful receipts. ChronOS currently uses bounded inline execution rather than a queue.

## Data lifecycle

Authenticated users can inventory and export owned planning, execution, memory, knowledge metadata, and integration data. Knowledge-source deletion atomically cascades chunks. Account deletion requires the exact confirmation phrase, inventories the data, removes Vault-backed Google secrets, and deletes the Auth user so ownership cascades remove ChronOS records. RPCs use a `pg_catalog` search path and restricted grants.

Trace retention defaults to 90 days and audit retention to 365 days. The service-role purge rejects unsafe short periods; scheduling it is an operator responsibility.

## Backup, recovery, and incidents

Managed backup and point-in-time recovery are hosting-platform responsibilities and are not claimed as tested. Local recovery is validated with forward migration reset, rollback tests, idempotent sync replay, interrupted-ingestion failed states, cached-context fallback, and reconnection. Account exports are versioned JSON for inspection; automated destructive restore is intentionally absent. Restore backups first to isolation, apply migrations, run schema/RLS checks, then switch traffic.

Incidents are correlated by request/workflow ID, classified by the shared taxonomy, and handled by containing retry storms, revoking affected connections/secrets, preserving safe audit metadata, and rechecking RLS. Private payloads must not be copied into incident systems.

## Legacy isolation

The backend no longer mounts legacy command, scheduling, drift, or backend demo route families. The frontend `/demo` route is a static public product preview and does not access user data or protected APIs. Today, Plan, Recovery, traces, and integrations use application services and repositories. The old `user_memory` table and compatibility Python modules remain isolated for data preservation and rollback analysis; active core routes do not depend on the legacy command, scheduling, or rescue graphs. Removal requires a separate verified retention decision.
