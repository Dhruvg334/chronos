# ChronOS — Implementation Plan

This document details the step-by-step implementation plan for ChronOS. It prioritizes a complete, working vertical loop (Mock Capacity -> Intake -> Risk -> Spine -> Command Canvas UI) before layering in Google OAuth, LangGraph, Drift detection, Rescue workflows, and Deployment.

---

## 1. Revised Dependency Order

To ensure early end-to-end feedback, the system is built in three stages:

```text
STAGE 1: The Core Vertical Loop (No Google OAuth block)
   [Supabase + Profile Triggers] 
              │
              ▼
   [Intake Logic (Gemini/Pydantic)] ───> [Risk Engine & Time Spine Nodes]
                                                    │
                                                    ▼
   [Command Canvas UI] <─── [Active Focus Console (Mock Calendar Capacity)]

STAGE 2: Calendar Integration & Agentic Orchestration
   [Google OAuth & Connections Table] ───> [Real Google Calendar Sync]
                                                      │
                                                      ▼
   [Multi-Mode LangGraph Modules] ───> [SSE Backend Agent Trace Stream]

STAGE 3: Dynamic Drift, Rescue, & Reflection
   [Drift Radar & Replan Graph] ───> [Decision Dock Approvals Table]
                                                │
                                                ▼
   [Rescue MVCP & Renegotiator] ───> [Reflections Engine & Memory Update Loop]
```

---

## 2. Revised Database Migration List (`/supabase/migrations/`)

Migrations must run in this exact order to satisfy foreign key relationships:

1. **`001_user_profiles.sql`**:
   - Creates the `user_profiles` table.
   - Adds the PostgreSQL trigger function that automatically inserts a profile row when a new user signs up via Supabase Auth (`auth.users`).
2. **`002_google_connections.sql`**:
   - Creates the `google_connections` table to store OAuth refresh tokens, credentials, and scopes separately from core user profiles.
3. **`003_commitments.sql`**:
   - Creates the `commitments` table with fields for deadline details, flexibility metrics, and risk estimates. Includes indexes on `(user_id, status)` and `deadline_at`.
4. **`004_tasks.sql`**:
   - Creates the `tasks` table storing sub-task actions associated with commitments.
5. **`005_time_spines.sql`**:
   - Creates the `time_spines` table storing checkpoint JSON arrays.
6. **`006_calendar_events.sql`**:
   - Creates the `calendar_events` table caching synced data.
   - Sets a compound unique constraint: `UNIQUE (user_id, google_event_id)` to isolate events across tenants.
7. **`007_focus_blocks.sql`**:
   - Creates the `focus_blocks` table storing dedicated capacity chunks (Deep Work, Buffer, etc.).
8. **`008_drift_events.sql`**:
   - Creates the `drift_events` table for logging plan deviations.
9. **`009_agent_runs.sql`**:
   - Creates the `agent_runs` table tracking LangGraph invocation jobs.
10. **`010_agent_trace_events.sql`**:
   - Creates the `agent_trace_events` table for granular server-side execution logs.
11. **`011_agent_proposed_actions.sql`**:
    - Creates the `agent_proposed_actions` table queuing actions for the Decision Dock.
12. **`012_reflections.sql`**:
    - Creates the `reflections` table logging focus metrics and notes.
13. **`013_user_memory.sql`**:
    - Creates the `user_memory` table tracking historical variance coefficients.

### System-Wide Database Triggers
All tables will include the following trigger to automate `updated_at` timestamps:
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

## 3. Revised API Router Contracts

### 3.1 Auth & Session (Vite Frontend Auth Guarding)
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/session` (extracts token and user profile)

### 3.2 Brain Dump & Structured Commitments
- `POST /api/v1/ai/intake`: Executes raw text extraction using the `intake_plan` node, validated with Pydantic. Saves approved commitments.
- `GET /api/v1/commitments`: Fetch active user commitments.
- `PATCH /api/v1/commitments/{id}`: Edit commitment metadata.

### 3.3 Calendar Configuration (Mocked during Stage 1)
- `GET /api/v1/calendar/auth-url`: Fetch Google OAuth authorization URL.
- `GET /api/v1/calendar/callback`: Redirect handler exchanging code for tokens.
- `GET /api/v1/calendar/events`: Sync Google Calendar events and local focus blocks.

### 3.4 Decision Dock Approvals
- `GET /api/v1/agent/proposed`: Fetches active `agent_proposed_actions` (e.g. proposed calendar moves).
- `POST /api/v1/agent/proposed/{id}/approve`: Approves a decision, triggering calendar writes.
- `POST /api/v1/agent/proposed/{id}/reject`: Rejects the action, removing it from the queue.

### 3.5 Drift Logging & Replanning
- `POST /api/v1/drift`: Logs a plan deviation and triggers the `drift_replan` node.
- `GET /api/v1/agent/runs/{id}/trace`: SSE (Server-Sent Events) endpoint streaming live execution trace events to the client.

### 3.6 Rescue & Negotiation
- `POST /api/v1/agent/rescue`: Triggers the rescue planning node (generates MVCP checklist).
- `POST /api/v1/agent/negotiate`: Generates context-based renegotiation templates.

### 3.7 Reflections
- `POST /api/v1/reflection`: Submits feedback for focus blocks and updates user memory.

---

## 4. Multi-Mode Agent & Validation Architecture

### Graph Modes
Instead of a monolithic router, we construct six dedicated graphs:
1. `intake_plan`: Raw text parser.
2. `drift_replan`: Compares focus blocks with calendar constraints and logs proposed changes to `agent_proposed_actions`.
3. `rescue`: Compiles MVCP steps when risk enters critical levels.
4. `negotiate`: Drafts custom communication scripts.
5. `reflect_update_memory`: Updates overrun coefficients.
6. `calendar_refresh`: Syncs Google Calendar data.

### LLM Structured Output Validation & Self-Repair Flow
1. **Validation**: Pydantic models validate raw JSON structures returned by Gemini API calls (e.g., matching the `CommitmentExtractor` schema).
2. **Error Catching**: Catch any validation exceptions (`ValidationError`).
3. **Repair Attempt**: Compile the original user input, the malformed model response, and the exact validation error messages. Send this back to Gemini in a structured prompt asking for correction.
4. **Safe Fallback**: If the corrected output fails validation again, abort the transaction, log a failed step in `agent_trace_events` with the validation error payload, and return a safe, default structured response (e.g., mapping raw inputs into generic Inbox cards marked for manual user completion) to prevent runtime crashes.

---

## 5. Development Phases & Verification Plan

### [COMPLETED] Phase 1: Local Setup & Core Database Schema
* **Files created**: `/supabase/migrations/*.sql`, `/backend/app/core/database.py`, `/docs/chronos/DB_VERIFICATION.md`
* **Tasks**: Scaffold directories. Initialize migrations. Connect backend to local Supabase.
* **Verification**: Run migrations. Confirm RLS blocks unauthenticated access and verify the auto-profile trigger adds profile rows upon registration.

### [COMPLETED] Phase 2: Core Vertical Loop (Mock Calendar Capacity)
* **Files created**: `/backend/app/api/v1/intake.py`, `/backend/app/schemas/intake.py`, `/backend/app/services/gemini_service.py`, frontend components (`ExtractionReview.tsx`, `CommitmentDraftCard.tsx`).
* **Tasks**: Implemented Brain Dump extraction using Gemini + Pydantic schema validation with a 1-retry repair loop. Built the Inbox UI page displaying parsed drafts. Implemented mock capacity calculation and deterministic risk scoring. Created the `/command` view.
* **Verification**: Verified using the automated pytest suite and manual testing on the local UI.

### [COMPLETED] Phase 3: Risk Modeling, Time Spine Engine, and Active Focus Console
* **Files created**: `/backend/app/services/risk_service.py`, `/backend/app/services/time_spine_service.py`, `/backend/app/api/v1/focus_blocks.py`, `/backend/app/api/v1/reflection.py`, `/frontend/src/pages/Command.tsx`
* **Tasks**: Coded the capacity calculator (remaining effort divided by available slots). Implemented Time Spine checkpoint generation and normalization. Assembled the Command Canvas layout. Built the Active Focus Console, incorporating manual block creation, start, complete (with reflection), and skip flows. Ensured atomic state updates.
* **Verification**: Verified using the automated pytest suite and manual testing on the local UI (Confirming risk recalculation logic and progress updates).

## Phase 4.5: Production Security Hardening (Completed)
**Goal:** Ensure all OAuth tokens are securely stored and no plaintext secrets leak into application tables or APIs.

- [x] Use Supabase Vault (`supabase_vault` extension) for token storage.
- [x] Remove plaintext `access_token` and `refresh_token` from `google_connections` table.
- [x] Build `SECURITY DEFINER` RPCs (`set_google_tokens`, `get_decrypted_google_tokens`, `delete_google_connection`) constrained to `service_role`.
- [x] Refactor backend `google_oauth_service.py` to route all token persistence and retrieval through these secure RPCs.
- [x] Audit endpoints (`GET /api/v1/google/connection`) to guarantee no secrets leak to frontend.
- [x] Verify tests pass without relying on plaintext tokens in Postgres.

### Phase 5: Auto-Scheduling (LangGraph MVP)Orchestration & SSE Traces
* **Files to create**: `/backend/app/agents/graph.py`, `/backend/app/api/v1/agent.py`
* **Tasks**: Wire up individual LangGraph graphs. Implement SSE progress streaming inside the Agent Console UI.
* **Verification**: Run an intake agent task and verify that the Agent Console displays live, server-sent trace steps in real time.

### Phase 7: Drift Radar & Replanning Agent
* **Files to create**: `/backend/app/api/v1/drift.py`, `/frontend/src/components/canvas/DecisionDock.tsx`
* **Tasks**: Build the drift event logging API. Configure the Replanner agent node to suggest calendar adjustments. Queue proposals in `agent_proposed_actions`.
* **Verification**: Log a drift event (e.g., "Overran task by 60 minutes"), confirm it triggers a recalculation, and verify that the proposed calendar shift appears in the Decision Dock.

### Phase 8: Rescue Mode & Renegotiation Templates
* **Files to create**: `/backend/app/api/v1/rescue.py`, `/frontend/src/pages/Rescue.tsx`
* **Tasks**: Implement the Rescue agent workflow (generating MVCP and quality tradeoffs). Build the Negotiator template generator.
* **Verification**: Manually trigger Rescue mode, verify that the MVCP checklist displays in the Rescue Terminal, and confirm it outputs copyable communication templates.

### Phase 9: Reflections Engine & Memory Calibration
* **Files to create**: `/backend/app/api/v1/reflection.py`, `/backend/app/agents/nodes/reflect.py`
* **Tasks**: Create the daily review questionnaire. Write the logic that calculates actual-vs-estimated variance and updates user memory.
* **Verification**: Submit three task reflections with consistent time overruns. Verify that subsequent estimations recommend adding a corresponding buffer percentage.

### Phase 10: Trace Audit, Polish, & Demo Scenarios
* **Files to create**: `/frontend/src/utils/demo_loader.ts`
* **Tasks**: Conduct UI polish passes ensuring warm light variables are applied consistently. Build the demo loaders for: Hackathon Week, Assignment Crisis, Interview Prep, and Busy Professional.
* **Verification**: Run each demo scenario from end to end. Confirm that risk levels recalculate, time spines redraw, and traces stream correctly.
