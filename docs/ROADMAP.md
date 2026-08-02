# Roadmap

## Core reliability completed

- Personal availability drives Today and Plan capacity without a universal workday assumption.
- Intake approval, focus completion, and recovery approval use idempotent PostgreSQL transactions with rollback coverage.
- Core time-spine, trace, and commitment-detail paths use repository protocols.
- Opt-in local Supabase coverage provisions two users and verifies migration, RLS, transactions, and the core journey.

## Next core hardening

- Move legacy scheduling/command and calendar-sync routes behind repositories when those surfaces re-enter the core journey.
- Run opt-in Supabase tests in a disposable CI service and add browser-level local-stack smoke coverage.
- Split shared vendor dependencies further if the entry bundle grows materially.

## Deliberately deferred

Projects, Insights, billing, desktop packaging, retrieval infrastructure, MCP, new integrations, advanced drag-and-drop planning, and autonomous external actions are outside the current core foundation.
