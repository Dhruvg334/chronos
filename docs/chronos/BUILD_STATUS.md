# ChronOS — Build Status Tracker

This document tracks the live implementation status of ChronOS core modules, database structures, APIs, and tests.

---

## 1. Phase 0: Scaffolding & Guardrails Status (Completed)

* **Repository Architecture**: Monorepo layout configured (`/frontend`, `/backend`, `/supabase`, `/docs`).
* **Docs & Assets**: Arch decisions, build status, deployment scripts, submission guidelines, `.env.example`, `.gitignore`, and `README.md` initialized.
* **Frontend Scaffolded**: React + TS + Vite with Tailwind CSS configuration, basic AppShell navigation, and placeholder pages:
  - Landing, Login, Signup, Command, Inbox, Calendar, Rescue, Reflection, Settings.
* **Backend Scaffolded**: FastAPI server with CORS middleware, Config loaders, health checks (`/api/v1/health`), and placeholder routes.
* **Supabase Scaffolded**: `supabase/migrations/` created with a structured migration execution plan and placeholder SQL files.

---

## 2. Intentionally Postponed (For Next Phase)
- **Database Tables & Triggers**: Real DDL migration runs (`001_create_user_profiles.sql` etc.) and PostgreSQL functions are not deployed.
- **Supabase & Auth Services**: Direct client integrations, session validation middleware, and RLS checks are mocked.
- **Google OAuth Flow**: The Google connection flow is simulated via simple API endpoint redirects.
- **LangGraph Agents & Tools**: The six agent graphs (`intake_plan`, `drift_replan`, etc.) are not operational yet.
- **Gemini Structured Validation**: Gemini output generation, schema validation, and repair loops are mocked.

---

## 3. Recommended Next Phase
* **Phase 1: Database Migration & Profile Setup**: Deploy migration scripts, write auth middleware, verify RLS policies, and enable auto-profile triggers.

---

## 4. Database Migrations (`/supabase/migrations/`)

| Migration File | Description | Status | RLS | Triggers |
|---|---|---|---|---|
| `001_user_profiles.sql` | Users profile definition & auto-creation trigger | 🟡 Placeholder | 🔴 Not Started | 🔴 Not Started |
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

*Status key: 🔴 Not Started | 🟡 In Development / Placeholder | 🟢 Completed & Verified*

---

## 5. Backend Modules & API Router (`/backend/`)

| Endpoint Module | Description | Status | Pydantic Validation | Test Coverage |
|---|---|---|---|---|
| `GET /api/v1/health` | Health Check Route | 🟢 Completed | N/A | 🔴 Not Started |
| `POST /api/v1/auth/signup` | Register new user in system | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/auth/login` | Login session verification | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/auth/session` | Get active session credentials | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/ai/intake` | Parse brain dump and generate Time Spine | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/commitments` | Retrieve commitment list | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/commitments` | Create manual structured commitment | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `PATCH /api/v1/commitments/{id}`| Edit commitment properties | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/calendar/auth-url` | Generate Google login link | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/calendar/callback` | Callback redirect to exchange OAuth codes | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/calendar/events` | Sync calendar capacity list | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/drift` | Log drift mismatch and run replanner | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/agent/proposed` | Fetch pending decisions for Decision Dock | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/agent/proposed/{id}/approve` | Confirm pending Decision Dock action | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/agent/rescue` | Manually activate Rescue plan | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/agent/negotiate` | Generate renegotiation script copy | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/reflection` | Submit focus block performance | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/agent/runs/{id}/trace`| Retrieve backend event streams | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |

---

## 6. LangGraph Orchestrations

| Graph Mode | Description | Status | Verification Status |
|---|---|---|---|
| `intake_plan` | Parses messy text, outputs Pydantic validated schema | 🔴 Not Started | 🔴 Not Started |
| `drift_replan` | Identifies schedule conflicts and logs actions to Dock | 🔴 Not Started | 🔴 Not Started |
| `rescue` | Generates minimum viable completions | 🔴 Not Started | 🔴 Not Started |
| `negotiate` | Resolves context into custom communication templates | 🔴 Not Started | 🔴 Not Started |
| `reflect_update_memory` | Computes historical overrun coefficients | 🔴 Not Started | 🔴 Not Started |
| `calendar_refresh` | Background OAuth capacity synchronization | 🔴 Not Started | 🔴 Not Started |

---

## 7. Frontend Command Canvas Components (`/frontend/`)

| Page / Component | Key UI Elements | Status | Mock State Hooked Up | API Hooked Up |
|---|---|---|---|---|
| `LandingPage.tsx` | Hero banner, demo selectors (Crisis, professional, etc.) | 🟢 Placeholder | 🟢 Completed | 🔴 Not Started |
| `AuthScreens` | Sign up, Log in, token handling | 🟢 Placeholder | 🟢 Completed | 🔴 Not Started |
| `AppShell.tsx` | Centered navbar, health badges, auth guarding | 🟢 Completed | 🟢 Completed | 🔴 Not Started |
| `InboxPage.tsx` | Large text area brain dump input, parsed approval cards | 🟢 Placeholder | 🟢 Completed | 🔴 Not Started |
| `TimeSpinePanel.tsx` | Dynamic SVG timeline with milestones and markers | 🟢 Placeholder | 🟢 Completed | 🔴 Not Started |
| `ActiveFocusConsole.tsx`| Current task details, done conditions, start cues, timer | 🟢 Placeholder | 🟢 Completed | 🔴 Not Started |
| `DriftRadar.tsx` | Logs list, custom drift logging form | 🟢 Placeholder | 🟢 Completed | 🔴 Not Started |
| `DecisionDock.tsx` | List of proposed agent actions requiring HitL approval | 🟢 Placeholder | 🟢 Completed | 🔴 Not Started |
| `AgentConsole.tsx` | Live streaming trace steps (SSE/polling based) | 🟢 Placeholder | 🟢 Completed | 🔴 Not Started |
| `CalendarPage.tsx` | Time block capacities grid, schedule allocations | 🟢 Placeholder | 🟢 Completed | 🔴 Not Started |
| `RescueTerminal.tsx` | Minimum Viable Completion sequence cards, renegotiator | 🟢 Placeholder | 🟢 Completed | 🔴 Not Started |
| `ReflectionPage.tsx` | Block/daily questionnaires, memory updates banners | 🟢 Placeholder | 🟢 Completed | 🔴 Not Started |
