# System Architecture

## Boundaries

The React frontend owns presentation and client interactions. TanStack Query owns server state and clears private cache data on logout. Supabase Auth owns browser sessions. Route pages load independently through `React.lazy`.

FastAPI owns authentication, deterministic planning, model access, bounded workflows, overlap and capacity validation, repositories, and integration adapters. `ApplicationContainer` constructs live clients lazily; imports do not open network clients.

Application code targets protocols in `app/repositories` and `app/models`. Supabase and Groq are adapters. The `core.database` facade remains only for historical paths listed below and must not be used by new core-journey code.

## Core journey

`GET /api/v1/today` composes active commitments, tasks, today’s cached calendar events, focus blocks, pending approvals, active focus state, one deterministic next action, optional recovery context, and at most one Strategy Engine recommendation.

`GET /api/v1/plan` composes calendar events, focus blocks, unscheduled commitments, an eight-hour capacity envelope, and transition buffers. `POST /api/v1/plan/blocks` validates ownership, overlap, and capacity before an explicit user-requested internal write.

Focus lifecycle endpoints create or start a session, persist pause/resume timing, expose deterministic stuck options, record completion reflection, update observed progress/risk, and invalidate Today/Plan queries in the UI. Recovery and reflection are contextual rather than primary routes.

## Persistence migration map

Repository-backed core paths: intake workflow runs and traces; approved commitment/task/time-spine writes; Today; Plan reads and block creation; focus lifecycle; contextual recovery proposals and approval; contextual reflection; core time-spine updates; trace viewing.

Compatibility access remains in historical commitment detail CRUD, legacy scheduling endpoints and graph, legacy command/demo data loaders, legacy rescue graph, standalone time-spine service, legacy trace service, calendar sync/event endpoints, and Google OAuth/calendar adapters. Today, Inbox approval, Plan, Focus, contextual recovery, and contextual reflection do not call those paths.

Migration `019_add_focus_session_lifecycle.sql` is forward-only and adds paused status, start/pause timestamps, accumulated pause seconds, and a stop reason. Existing applied migrations remain unchanged.
