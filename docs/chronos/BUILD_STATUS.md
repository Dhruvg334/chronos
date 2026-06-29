# ChronOS — Build Status Tracker

This document tracks the live implementation status of ChronOS core modules, database structures, APIs, and tests.

---

## 1. Overall Status
- **Phase 0:** Scaffolding & Guardrails - 🟢 Completed
- [x] **Phase 1**: Core Database schema, isolated user contexts, auth integrations.
- [x] **Phase 2**: AI Extraction & Pydantic validation loops.
- [x] **Phase 3**: Active Focus Console, reflection loops, dynamic risk engines.
- [x] **Phase 4**: Real-time mock APIs mapped to Google Calendar & Free/Busy Sync.
- [x] **Phase 4.5**: Production Security Hardening (Supabase Vault for OAuth tokens).
- [ ] **Phase 5**: Agentic Auto-Scheduling (LangGraph) & Eventual Rescheduling loops.
- [ ] **Phase 6**: Rescue Mode & Chaos handling.Started

---

## 2. Database Migrations (`/supabase/migrations/`)

| Migration File | Description | Status | RLS | Triggers |
|---|---|---|---|---|
| `001_user_profiles.sql` | Users profile definition & auto-creation trigger | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `002_google_connections.sql` | Encrypted Google credential storage | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `003_commitments.sql` | Core commitments storage and indexes | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `004_tasks.sql` | Next actions and breakdown lists | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `005_time_spines.sql` | Structured checkpoint arrays | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `006_calendar_events.sql` | Synced event cache | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `007_focus_blocks.sql` | Dedicated calendar capacity blocks | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `008_drift_events.sql` | Logged plan deviations | 🟢 Completed | 🟢 Enforced | N/A |
| `009_agent_runs.sql` | LangGraph run checkpoints | 🟢 Completed | 🟢 Enforced | N/A |
| `010_agent_trace_events.sql`| Granular backend action trace entries | 🟢 Completed | 🟢 Enforced | N/A |
| `011_agent_proposed_actions`| Decision Dock approvals queue | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `012_reflections.sql` | Post-block estimation feedback | 🟢 Completed | 🟢 Enforced | N/A |
| `013_user_memory.sql` | Historical coefficient updates | 🟢 Completed | 🟢 Enforced | 🟢 Hooked |
| `014_grant_api_role_privileges.sql` | Grants authenticated and service_role | 🟢 Completed | N/A | N/A |

---

## 3. Backend Modules & API Router (`/backend/`)

| Endpoint Module | Description | Status | Pydantic Validation | Test Coverage |
|---|---|---|---|---|
| `GET /api/v1/health` | Health Check Route | 🟢 Completed | N/A | 🟢 Completed |
| `POST /api/v1/intake` | Parse brain dump and generate Time Spine | 🟢 Completed | 🟢 Completed | 🟢 Completed |
| `GET /api/v1/commitments` | Retrieve commitment list | 🟢 Completed | 🟢 Completed | 🟢 Completed |
| `GET /api/v1/commitments/{id}` | Retrieve commitment detail, spine, & blocks | 🟢 Completed | 🟢 Completed | 🟢 Completed |
| `POST /api/v1/focus-blocks` | Create manual structured focus block | 🟢 Completed | 🟢 Completed | 🟢 Completed |
| `POST /api/v1/focus-blocks/{id}/start` | Mark focus block active | 🟢 Completed | N/A | 🟢 Completed |
| `POST /api/v1/focus-blocks/{id}/complete` | Submit focus block performance (atomically inserts reflection) | 🟢 Completed | 🟢 Completed | 🟢 Completed |
| `POST /api/v1/focus-blocks/{id}/skip` | Skip focus block with penalty | 🟢 Completed | 🟢 Completed | 🟢 Completed |
| `POST /api/v1/reflection` | Submit standalone reflection | 🟢 Completed | 🟢 Completed | 🟢 Completed |
| `GET /api/v1/calendar/*` | Google login & calendar sync | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/drift` | Log drift mismatch and run replanner | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `GET /api/v1/agent/proposed` | Fetch pending decisions for Decision Dock | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |
| `POST /api/v1/agent/rescue` | Manually activate Rescue plan | 🟡 Mocked | 🔴 Not Started | 🔴 Not Started |

---

## 4. Frontend Application (`/frontend/`)

| Feature | Description | Status | Typescript Types |
|---|---|---|---|
| Command Canvas | `Command.tsx` - Details, Time Spine, Focus Console | 🟢 Completed | 🟢 Enforced |
| Inbox / AI Intake | `Inbox.tsx` - AI Brain Dump to Structured Drafts | 🟢 Completed | 🟢 Enforced |
| Landing Page | `Landing.tsx` - Placeholder structure | 🟢 Completed | 🟢 Enforced |
| Calendar/Rescue | Mock layouts | 🟡 Mocked | 🔴 Not Started |
