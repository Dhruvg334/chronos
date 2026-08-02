---
name: architecture-review
description: Review ChronOS architecture changes for boundary violations, coupling, compatibility impact, migration risk, security regressions, and testability. Use before structural refactors, new infrastructure, service integrations, persistence changes, or cross-layer features.
---

# Architecture Review

## Required inputs

- Requested behavior and affected user flow
- Current call paths, protocols, configuration, tests, and migrations
- Compatibility and data-migration expectations

## Workflow

1. Read `AGENTS.md` and the relevant architecture/security documents.
2. Map entry points, dependencies, state ownership, external calls, and security boundaries.
3. Identify import-time construction, direct adapter calls, duplicated state, unvalidated data, and unbounded operations.
4. State compatibility impact and migration risk before editing.
5. Prefer protocols, dependency injection, deterministic validators, and forward migrations.
6. Add tests at the boundary being changed.

## Checks

- No live client is created during import.
- Domain/application code does not depend on provider SDKs or direct Supabase chains.
- Auth identity, RLS, approval, idempotency, timeout, and error behavior remain explicit.
- Documentation distinguishes implemented behavior from roadmap.

## Commands

Run `rg -n "create_client|\.table\(|httpx|fetch\(" backend frontend`, backend tests, and frontend type-check/tests/build as applicable.

## Expected output

Provide findings by severity, an architecture map, compatibility/migration impact, exact files changed, and verification output.

## Stop conditions

Stop before a destructive migration, weakened auth/RLS, new external mutation without approval, or a change requiring unavailable production credentials.
