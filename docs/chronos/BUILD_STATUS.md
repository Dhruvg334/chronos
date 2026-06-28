# ChronOS — Build Status Tracker

This document tracks the live implementation status of ChronOS core modules, database structures, APIs, and tests.

---

## 1. Phase 0: Scaffolding & Guardrails Status (Completed)
- Monorepo folder layouts, configurations, basic pages, routing shell, FastAPI Cors setup, health routers completed.

---

---

## 4. Database Migrations (`/supabase/migrations/`)

| Migration File | Description | Status | RLS | Triggers |
|---|---|---|---|---|
| `001_user_profiles.sql` | Users profile definition & auto-creation trigger | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `002_google_connections.sql` | Encrypted Google credential storage | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `003_commitments.sql` | Core commitments storage and indexes | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `004_tasks.sql` | Next actions and breakdown lists | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `005_time_spines.sql` | Structured checkpoint arrays | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `006_calendar_events.sql` | Synced event cache with compound unique constraint | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `007_focus_blocks.sql` | Dedicated calendar capacity blocks | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `008_drift_events.sql` | Logged plan deviations | 🟢 Completed | 🟢 Enforced | N/A |
| `009_agent_runs.sql` | LangGraph run checkpoints | 🟢 Completed | 🟢 Enforced | N/A |
| `010_agent_trace_events.sql`| Granular backend action trace entries | 🟢 Completed | 🟢 Enforced | N/A |
| `011_agent_proposed_actions`| Decision Dock approvals queue | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `012_reflections.sql` | Post-block estimation feedback | 🟢 Completed | 🟢 Enforced | N/A |
| `013_user_memory.sql` | Historical coefficient updates | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |

---

## 5. Backend Modules & API Router (`/backend/`)

| Endpoint Module | Description | Status | Pydantic Validation | Test Coverage |
|---|---|---|---|---|
| `GET /api/v1/health` | Health Check Route (Database connectivity checked) | 🟢 Completed | N/A | 🔴 Not Started |
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
