---
name: release-validation
description: Validate ChronOS dependency installation, offline backend tests, frontend type-check/lint/tests/build, health endpoints, security invariants, documentation accuracy, repository wording, and manual profiles. Use before handoff or release readiness claims.
---

# Release Validation

## Required inputs

- Intended change scope
- Current working-tree status
- Required automated and manual profiles

## Workflow

1. Inspect `git status` without discarding user changes.
2. Recreate clean environments where practical; use authoritative lock/manifests.
3. Run backend install, default tests, opt-in integration marker, import, and health smoke checks.
4. Run frontend `npm ci`, type-check, lint, tests, and build.
5. Search for live clients, deprecated provider coupling, secret exposure, stale wording, and route regressions.
6. Verify docs match actual behavior and list limitations.

## Checks

- Default backend tests make no external connection attempts.
- Frontend install uses no force or legacy-peer flags.
- No service-role key reaches frontend code.
- Applied migrations are unchanged.
- Public demo is isolated; protected routes do not flash data.
- No automatic commit or push occurred.

## Commands

Use the exact command sets in `docs/engineering/TESTING.md`, plus `git diff --check`, `git status --short`, and targeted `rg` security/wording scans.

## Expected output

Report exact outputs, manual checks, integration status, security findings, limitations, deferred work, next-phase safety, and one unique suggested commit message.

## Stop conditions

Do not declare success while required checks fail, build errors remain, secrets appear, unit tests reach live services, or security boundaries are weakened.
