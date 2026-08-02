# System Architecture

## Boundaries

The React frontend owns presentation and client interactions. TanStack Query owns server state and clears private cache data on logout. Supabase Auth owns browser sessions. Route pages load independently through `React.lazy`.

FastAPI owns authentication, deterministic planning, model access, bounded workflows, overlap and capacity validation, repositories, and integration adapters. `ApplicationContainer` constructs live clients lazily; imports do not open network clients.

Application code targets protocols in `app/repositories` and `app/models`. Supabase and Groq are adapters. The `core.database` facade remains only for historical paths listed below and must not be used by new core-journey code.

## Core journey

`GET /api/v1/today` composes active commitments, tasks, today’s cached calendar events, focus blocks, pending approvals, active focus state, one deterministic next action, optional recovery context, and at most one Strategy Engine recommendation.

`GET /api/v1/plan` composes calendar events, focus blocks, unscheduled commitments, and profile-driven capacity. The deterministic engine applies the user's IANA timezone, available weekdays, working window, protected interval, daily focus limit, transition buffer, unscheduled reserve, calendar state, and deadline window. It returns remaining and over-capacity minutes with confidence and source metadata. `POST /api/v1/plan/blocks` validates ownership, availability, protected time, transitions, overlap, and capacity before a write.

Focus lifecycle endpoints create or start a session, persist pause/resume timing, expose deterministic stuck options, record completion reflection, update observed progress/risk, and invalidate Today/Plan queries in the UI. Recovery and reflection are contextual rather than primary routes.

## Persistence migration map

Repository-backed core paths: intake workflow runs and traces; approved commitment/task/time-spine writes; commitment list/detail; Today; Plan; focus lifecycle; contextual recovery; contextual reflection; planning profiles; core time-spine updates; and trace viewing. Application services do not import the compatibility Supabase client.

Compatibility access remains in legacy calendar, command, and scheduling API modules; the legacy scheduling and rescue graphs; and Google OAuth/calendar infrastructure adapters. These paths are outside Today, Inbox approval, Plan, Focus, contextual recovery, contextual reflection, and commitment detail. The compatibility client also remains at the API dependency construction boundary until historical routes move to the application container.

Migration 019 adds focus lifecycle state, migration 020 adds the planning profile, and migration 021 adds idempotent transaction RPCs and operation receipts. Intake approval, focus completion, and recovery approval perform their related writes atomically in PostgreSQL.
