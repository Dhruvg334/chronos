# Roadmap

## Core reliability completed

- Personal availability drives Today and Plan capacity without a universal workday assumption.
- Intake approval, focus completion, and recovery approval use idempotent PostgreSQL transactions with rollback coverage.
- Core time-spine, trace, and commitment-detail paths use repository protocols.
- Opt-in local Supabase coverage provisions two users and verifies migration, RLS, transactions, and the core journey.
- Adaptive intake preserves uncertainty and dependency evidence; adaptive planning and recovery use bounded model calls followed by deterministic validation.
- Read-only Google events contribute to capacity with live/cached/stale/unavailable provenance, confidence, last sync, and retry behavior.
- Atomic adaptive-plan approval is available through migration 022, and compact user-facing explanations preserve the approval boundary.

## Next core hardening

- Move the remaining legacy scheduling/command provider adapters behind repositories when those surfaces re-enter the core journey.
- Run credentialed Groq and Google opt-in suites in an approved disposable environment; local implementation currently skips them when credentials are absent.
- Run opt-in Supabase tests in a disposable CI service and add browser-level local-stack smoke coverage.
- Split shared vendor dependencies further if the entry bundle grows materially.

## Deliberately deferred

Projects, Insights, billing, desktop packaging, retrieval infrastructure, MCP, new integrations, advanced drag-and-drop planning, and autonomous external actions are outside the current core foundation.
