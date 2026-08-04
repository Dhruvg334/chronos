# Integration Model

ChronOS external context is read-first, user-owned, provenance-tagged, and optional. Provider SDKs and OAuth payloads remain inside adapters. Application services depend on `ExternalConnector`, normalized repository protocols, and the centralized tool-permission model. Imports do not create clients or open network connections.

## Persistence and normalization

Migration 027 adds integration connections, normalized items, action proposals, and concise audit events. A connection stores status, granted scopes, a backend-only token reference, timestamps, a bounded cursor, and allow-listed sync metadata. It never stores a raw token. Items use provider/external identity for idempotent upsert and retain a bounded summary, safe URL, dates, project association, checksum, allow-listed metadata, synchronization time, and tombstone. Provider deletion removes only provider-owned calendar cache; it never deletes a user-authored commitment, outcome, memory, or note.

Action proposals are approval-first internal records. Gmail, GitHub, Notion, and Planner context can propose an Inbox classification, but nothing silently becomes a commitment, outcome, event, reference, or memory. Approved internal creation uses the owner-validating transaction; no external provider mutation executor exists.

## Connector contract and synchronization

Connectors declare capabilities, required scopes, permission classes, and data accessed. The common contract covers authorization URL/callback where implemented, status, refresh/revocation, incremental synchronization, bounded detail, health, pagination/cursors, and classified failure. Synchronization is capped at 10 pages of 100 normalized items. Timeout, rate-limit, revoked, expired, invalid-response, and unavailable states are safe classifications. On failure, the connection becomes degraded/expired/revoked and cached context remains usable.

Provider content is untrusted data. It may inform Inbox proposals or bounded context packs, but cannot authorize tools, alter instructions, or bypass deterministic planning, ownership, capacity, overlap, dependency, or approval checks. Logs and audits contain counts, provider, classification, request/workflow IDs, and tool names—not tokens, full messages, raw documents, provider payloads, or hidden reasoning.

## Capability matrix

| Provider | Implemented read surface | Selection boundary | Writes |
|---|---|---|---|
| Google Calendar | OAuth, Vault tokens, events, free/busy, recurrence/cancellation/timezone normalization, cached fallback | Primary calendar | Disabled |
| Gmail | Bounded message normalization, reply/signature reduction, deadline/dependency proposals | Authorized account; attachments excluded | Sending, drafting, deleting, archiving, labels disabled |
| GitHub | Repository metadata, issues, PR/milestone/release/activity-shaped normalization | Explicit repository allow-list | Disabled |
| Notion | Bounded page/database context | Explicit selected resources | Disabled |
| Outlook Calendar | Event/free-busy-shaped contract and timezone normalization | Selected calendars | Disabled |
| Obsidian | User-selected Markdown file or ZIP import through knowledge ingestion | Files explicitly uploaded | No filesystem/background sync |
| Microsoft Planner | Plans, buckets, tasks, due dates, assignments, completion-shaped normalization | Selected plans | Disabled |

Only Google Calendar has an existing live OAuth flow. Other provider adapters, configuration states, offline fakes, normalization, and tests are implemented; live OAuth exchange is not claimed without disposable credentials.

## MCP and permission boundary

The authenticated ChronOS MCP server exposes application-service tools only: read Today, read one owned project summary, list pending approvals, propose an Inbox item, and propose a plan adjustment. It exposes no SQL, table client, token, vector, unrestricted context search, or direct write.

The client foundation requires an exact HTTPS hostname allow-list, port 443, no URL credentials, no private/loopback/link-local literal addresses, enabled server configuration, declared tools, validated schemas, allowed permissions, timeout, and request budget. Proposal tools return pending approval; approved-write classes and prohibited/undeclared writes are rejected. Retrieved MCP text is untrusted and cannot expand capability.

The centralized classes are `read_internal`, `read_external`, `propose_internal_write`, `approved_internal_write`, `propose_external_write`, `approved_external_write`, and `prohibited`. Tools can declare scopes, data access, approval, idempotency, audit category, timeout, and rollback behavior.

## Configuration and testing

Backend-only variables include Google, Gmail, GitHub, Notion, and Microsoft OAuth identifiers/secrets; integration timeout/retry/page bounds; and `MCP_ALLOWED_SERVERS`, timeout, and request budget. No integration secret belongs in Vite variables or frontend bundles.

Default tests use adapters and in-memory repositories without Docker, ports, OAuth, or network access. Migration/RLS tests are opt-in through the existing local Supabase variables. Live provider tests require explicit flags and disposable accounts and must report exactly which provider path ran.
