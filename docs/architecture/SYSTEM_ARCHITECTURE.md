# System Architecture

## Boundaries

The React frontend owns presentation and client interactions. TanStack Query owns server state and clears private cache data on logout. Supabase Auth owns browser sessions. Route pages load independently through `React.lazy`.

FastAPI owns authentication, deterministic planning, model access, bounded workflows, overlap and capacity validation, repositories, and integration adapters. `ApplicationContainer` constructs live clients lazily; imports do not open network clients.

Groq is accessed only through the provider-neutral `ModelGateway`. Structured responses receive Pydantic validation and at most one bounded repair request. Intake, adaptive planning, and adaptive recovery reserve that repair inside their workflow request budgets. Provider prompts and raw responses are not written to traces or logs.

Application code targets protocols in `app/repositories` and `app/models`. Supabase and Groq are adapters. The `core.database` facade remains only for historical paths listed below and must not be used by new core-journey code.

## Core journey

`GET /api/v1/today` composes active commitments, tasks, project/outcome context for the next action, routine occurrences due today, today’s cached calendar events, focus blocks, pending approvals, active focus state, one deterministic next action, optional recovery context, and at most one Strategy Engine recommendation.

`GET /api/v1/plan` composes calendar events, focus blocks, unscheduled commitments, and profile-driven capacity. The deterministic engine applies the user's IANA timezone, available weekdays, working window, protected interval, daily focus limit, transition buffer, unscheduled reserve, calendar state, and deadline window. It returns remaining and over-capacity minutes with confidence and source metadata. `POST /api/v1/plan/blocks` validates ownership, availability, protected time, transitions, overlap, and capacity before a write.

`POST /api/v1/plan/adaptive` loads the same deterministic context, asks the model for at most three small candidate plans, rejects dependency, overlap, availability, deadline, and capacity violations, and persists only the best valid pending proposal. Approval revalidates current state and migration 022 applies all proposed focus blocks plus proposal/trace state atomically.

Adaptive recovery uses deterministic evidence to classify overload, interruption, ambiguity, dependency blocking, underestimated duration, start friction, sufficiently evidenced low energy, or calendar disruption. The model may phrase at most three options; feasibility remains deterministic. Provider failure degrades to one deterministic option without external action.

Project, outcome, and routine application services depend on dedicated repository protocols. Projects expose product-oriented progress and next-action summaries; outcomes remain completed-state records and can own existing commitments/tasks; routines derive due occurrences from weekday and preferred-time rules. `/api/v1/week` combines these records with profile capacity, calendar events, protected intervals, buffers, and existing blocks. Weekly suggestions are deterministic, editable, rejectable, and require approval; current-state validation runs again before migration 024 atomically creates blocks.

Calendar capacity distinguishes live, cached, stale, unavailable, disconnected, and configuration-missing states. Fresh or cached Google events remain read-only. Stale/provider-unavailable states expose reduced confidence and retry; disconnected planning ignores Google cache while retaining local events.

Focus lifecycle endpoints create or start a session, persist pause/resume timing, expose deterministic stuck options, record completion reflection, update observed progress/risk, and invalidate Today/Plan queries in the UI. Recovery and reflection are contextual rather than primary routes.

## Persistence migration map

Repository-backed core paths: intake workflow runs and traces; approved commitment/task/time-spine writes; commitment list/detail; Today; Plan; focus lifecycle; contextual recovery; contextual reflection; planning profiles; core time-spine updates; and trace viewing. Application services do not import the compatibility Supabase client.

Compatibility access remains in legacy calendar, command, and scheduling API modules; the legacy scheduling and rescue graphs; and Google OAuth/calendar infrastructure adapters. These paths are outside Today, Inbox approval, Plan, Focus, contextual recovery, contextual reflection, and commitment detail. The compatibility client also remains at the API dependency construction boundary until historical routes move to the application container.

Migration 019 adds focus lifecycle state, migration 020 adds the planning profile, migration 021 adds core idempotent transaction RPCs and operation receipts, migration 022 adds atomic adaptive-plan approval, migration 023 hardens its definer boundary, and migration 024 adds projects, outcomes, routines, routine occurrences, weekly plans, optional commitment/task links, mixed-item intake approval, and atomic weekly-plan approval. Intake approval, focus completion, recovery approval, adaptive-plan approval, and weekly-plan approval perform their related writes atomically in PostgreSQL.
