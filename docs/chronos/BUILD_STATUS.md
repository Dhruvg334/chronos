# ChronOS — Build Status Tracker

This document tracks the live implementation status of ChronOS core modules, database structures, APIs, and tests.

---

## 1. Database migrations (`/supabase/migrations/`)

| Migration File | Description | Status | RLS | Triggers |
|---|---|---|---|---|
| `001_user_profiles.sql` | Users profile definition & auto-creation trigger | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `002_google_connections.sql` | Encrypted Google credential storage | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `003_commitments.sql` | Core commitments storage and indexes | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `004_tasks.sql` | Next actions and breakdown lists | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `005_time_spines.sql` | Structured checkpoint arrays | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `006_calendar_events.sql` | Synced event cache with compound unique constraint | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `007_focus_blocks.sql` | Dedicated calendar capacity blocks | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `008_drift_events.sql` | Logged plan deviations | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `009_agent_runs.sql` | LangGraph run checkpoints | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `010_agent_trace_events.sql`| Granular backend action trace entries | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `011_agent_proposed_actions`| Decision Dock approvals queue | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `012_reflections.sql` | Post-block estimation feedback | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `013_user_memory.sql` | Historical coefficient updates | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |

*Status key: 🔴 Not Started | 🟡 In Development | 🟢 Completed & Verified*

---

## 2. Backend Modules & API Router (`/backend/`)

| Endpoint Module | Description | Status | Pydantic Validation | Test Coverage |
|---|---|---|---|---|
| `POST /api/v1/auth/signup` | Register new user in system | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/auth/login` | Login session verification | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/auth/session` | Get active session credentials | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/ai/intake` | Parse brain dump and generate Time Spine | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/commitments` | Retrieve commitment list | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/commitments` | Create manual structured commitment | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `PATCH /api/v1/commitments/{id}`| Edit commitment properties | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/calendar/auth-url` | Generate Google login link | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/calendar/callback` | Callback redirect to exchange OAuth codes | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/calendar/events` | Sync calendar capacity list | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/drift` | Log drift mismatch and run replanner | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/agent/proposed` | Fetch pending decisions for Decision Dock | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/agent/proposed/{id}/approve` | Confirm pending Decision Dock action | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/agent/rescue` | Manually activate Rescue plan | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/agent/negotiate` | Generate renegotiation script copy | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/reflection` | Submit focus block performance | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/agent/runs/{id}/trace`| Retrieve backend event streams | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |

---

## 3. LangGraph Orchestrations

| Graph Mode | Description | Status | Verification Status |
|---|---|---|---|
| `intake_plan` | Parses messy text, outputs Pydantic validated schema | 🔴 Not Started | 🔴 Not Started |
| `drift_replan` | Identifies schedule conflicts and logs actions to Dock | 🔴 Not Started | 🔴 Not Started |
| `rescue` | Generates minimum viable completions | 🔴 Not Started | 🔴 Not Started |
| `negotiate` | Resolves context into custom communication templates | 🔴 Not Started | 🔴 Not Started |
| `reflect_update_memory` | Computes historical overrun coefficients | 🔴 Not Started | 🔴 Not Started |
| `calendar_refresh` | Background OAuth capacity synchronization | 🔴 Not Started | 🔴 Not Started |

---

## 4. Frontend Command Canvas Components (`/frontend/`)

| Page / Component | Key UI Elements | Status | Mock State Hooked Up | API Hooked Up |
|---|---|---|---|---|
| `LandingPage.tsx` | Hero banner, demo selectors (Crisis, professional, etc.) | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `AuthScreens` | Sign up, Log in, token handling | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `AppShell.tsx` | Centered navbar, health badges, auth guarding | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `InboxPage.tsx` | Large text area brain dump input, parsed approval cards | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `TimeSpinePanel.tsx` | Dynamic SVG timeline with milestones and markers | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `ActiveFocusConsole.tsx`| Current task details, done conditions, start cues, timer | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `DriftRadar.tsx` | Logs list, custom drift logging form | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `DecisionDock.tsx` | List of proposed agent actions requiring HitL approval | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `AgentConsole.tsx` | Live streaming trace steps (SSE/polling based) | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `CalendarPage.tsx` | Time block capacities grid, schedule allocations | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `RescueTerminal.tsx` | Minimum Viable Completion sequence cards, renegotiator | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
| `ReflectionPage.tsx` | Block/daily questionnaires, memory updates banners | 🔴 Not Started | 🔴 Not Started | 🔴 Not Started |
