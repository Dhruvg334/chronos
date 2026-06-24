# Chronos — Project Requirements Document

> Product: **ChronOS**  
> Type: Proactive AI time operating system  
> Primary problem statement: The Last-Minute Life Saver  
> Build attitude: real product architecture; hackathon submission is first release, not the ceiling.

---

## 1. Project Overview

ChronOS is a proactive AI time operating system for managing commitments across their full lifecycle. It uses agentic AI, Google Calendar intelligence, deadline-risk modeling, and adaptive replanning to help users complete important work before deadlines fail.

---

## 2. Goals

### 2.1 Primary Goals

- Convert messy commitments into structured plans.
- Detect deadline risk before the user notices failure.
- Build adaptive time-spines from commitment creation to completion.
- Use Google Calendar as a real constraint layer.
- Use LangGraph-based agentic AI for planning, replanning, rescue, negotiation, and reflection.
- Provide explainable agent actions through an Agent Trace Panel.
- Deliver a polished warm-light UX with a dynamic Command Canvas.

### 2.2 Secondary Goals

- Track estimate-vs-actual behavior.
- Learn task-type overrun factors.
- Support deep work and feedback gates.
- Help users renegotiate impossible commitments.
- Maintain robust auth and user-scoped data with Supabase.
- Deploy through Google AI Studio / Google Cloud.

---

## 3. Success Criteria

ChronOS succeeds if a user can:

1. Sign up and log in.
2. Connect Google Calendar.
3. Brain-dump messy commitments.
4. See structured commitments extracted by Gemini.
5. Approve/edit extracted commitments.
6. See a dynamic Time Spine.
7. See risk scores and explanations.
8. Simulate or log drift events.
9. Watch ChronOS replan.
10. Approve calendar focus blocks.
11. Enter Rescue Mode for critical commitments.
12. Generate a renegotiation message.
13. Complete a focus block and log reflection.
14. See agent traces for major AI/tool actions.

---

## 4. User Personas

### 4.1 Student Builder

Needs:

- assignment planning,
- project deadlines,
- hackathon execution,
- interview prep,
- exam scheduling.

### 4.2 Professional Operator

Needs:

- meeting-aware planning,
- deadline tracking,
- follow-up management,
- deep-work protection,
- rescheduling support.

### 4.3 Founder / Creator

Needs:

- multi-project execution visibility,
- priority tradeoff clarity,
- adaptive weekly planning,
- urgent vs important separation.

---

## 5. Functional Requirements

## 5.1 Authentication

### Requirement

Users must be able to create accounts and access private workspaces.

### Implementation

- Supabase Auth
- Email/password
- Optional Google OAuth
- Protected frontend routes
- Backend session/user validation
- RLS-backed user data isolation

### Acceptance Criteria

- User can sign up.
- User can log in.
- User can log out.
- User cannot access another user’s data.
- Private routes redirect unauthenticated users.

---

## 5.2 User Profile and Preferences

### Requirement

ChronOS must store planning preferences.

### Fields

- timezone
- working hours
- preferred deep-work windows
- preferred shallow-work windows
- energy pattern
- focus duration preference
- default buffer percentage
- autonomy level
- calendar write permission status

### Acceptance Criteria

- User can create/update preferences.
- Scheduling uses preferences.
- Preferences persist after reload.

---

## 5.3 Brain Dump Intake

### Requirement

User can enter messy natural-language input and ChronOS extracts commitments.

### Input Types

- plain text
- bulk paste
- optional browser voice input
- demo scenario

### Extracted Output

Each item should include:

- title
- description
- type
- deadline
- estimated effort
- priority
- consequence
- flexibility
- dependencies
- next action
- done condition
- missing information
- confidence score

### AI Requirement

Gemini must return structured JSON validated with backend schemas.

### Acceptance Criteria

- A paragraph with multiple tasks produces multiple structured commitments.
- User can approve, edit, or reject each extracted item.
- Uncertain fields are visibly marked.

---

## 5.4 Commitment Management

### Requirement

Users can manage commitments.

### Commitment Types

- hard deadline
- soft deadline
- event
- habit
- waiting-on
- recurring obligation
- reference
- someday

### Commitment Status

- inbox
- clarified
- planned
- active
- blocked
- at-risk
- rescue
- completed
- archived

### Acceptance Criteria

- Users can create, update, complete, archive, and delete commitments.
- Commitment detail view shows risk, next action, time spine, related blocks, and reflections.

---

## 5.5 Next Action Compiler

### Requirement

ChronOS converts vague commitments into concrete next actions.

### Output

- immediate next action
- expected duration
- done condition
- required materials/context
- blocked condition
- two-minute starter step

### Acceptance Criteria

- Every active commitment has one current next action.
- User can regenerate or edit next action.
- Active Focus Console always has a clear action.

---

## 5.6 Google Calendar Integration

### Requirement

Google Calendar must be a first-class feature.

### Capabilities

- Google OAuth connection
- fetch upcoming calendar events
- detect busy/free windows
- create ChronOS focus blocks
- create rescue blocks
- update ChronOS-created blocks
- avoid editing non-ChronOS events without explicit approval

### Acceptance Criteria

- User can connect Google Calendar.
- ChronOS fetches events.
- ChronOS identifies available windows.
- ChronOS proposes focus blocks.
- User approves calendar writes.
- Calendar actions are logged in Agent Trace.

---

## 5.7 Time Spine Engine

### Requirement

ChronOS must generate time-spines for significant commitments.

### Spine Stages

- capture
- clarify
- start-before
- milestone
- feedback gate
- buffer
- finalization
- deadline
- reflection

### Acceptance Criteria

- Major commitments show a visual time spine.
- Spine updates after deadline/progress/calendar changes.
- Risk zones appear on the spine.
- User can inspect why a checkpoint exists.

---

## 5.8 Risk Engine

### Requirement

ChronOS must calculate risk for each active commitment.

### Risk Inputs

- time remaining
- effort remaining
- calendar availability
- progress percent
- dependencies
- task difficulty
- energy match
- user overrun factor
- consequence
- flexibility

### Risk Levels

- Stable
- Watch
- At Risk
- Critical
- Rescue Required

### Acceptance Criteria

- Each commitment has a risk score and risk level.
- Risk recalculates after drift events.
- Risk explanation is user-readable.
- Critical tasks suggest Rescue Mode.

---

## 5.9 Command Canvas

### Requirement

The main interface must be an interactive Command Canvas, not a static table.

### Zones

1. Time Spine Panel
2. Active Focus Console
3. Agent Console
4. Drift Radar
5. Decision Dock
6. Calendar Layer

### Acceptance Criteria

- User sees current mission.
- User sees upcoming risk.
- User can log drift.
- User can approve/reject replans.
- User can inspect agent trace.

---

## 5.10 Drift Radar

### Requirement

ChronOS must detect and log drift events.

### Drift Types

- task overrun
- task underrun
- skipped block
- new event
- event overrun
- low energy
- dependency blocked
- scope increase
- deadline changed

### Acceptance Criteria

- User can manually log drift.
- Calendar changes can generate drift.
- Drift triggers risk recalculation.
- Drift can trigger replanning.

---

## 5.11 Replanner Agent

### Requirement

ChronOS must adapt plans after drift.

### Replanning Actions

- move flexible tasks
- preserve hard deadlines
- protect deep work
- insert buffers
- compress shallow work
- defer low-impact tasks
- trigger rescue
- ask for approval

### Acceptance Criteria

- Replanner responds to at least four drift types.
- Replanner explains tradeoffs.
- User can accept, reject, or modify replan.
- Agent trace logs every replan step.

---

## 5.12 Rescue Mode

### Requirement

ChronOS must provide an emergency workflow for critical commitments.

### Rescue Modes

- 30-minute rescue
- 90-minute rescue
- tonight rescue
- before tomorrow
- submission sprint

### Output

- crisis summary
- minimum viable completion path
- must-do sequence
- skip list
- quality tradeoffs
- required focus blocks
- final checklist
- renegotiation option

### Acceptance Criteria

- Critical commitment can enter Rescue Mode.
- Rescue plan is generated and schema-validated.
- User gets a first action immediately.
- Checklist is interactive.

---

## 5.13 Negotiator Agent

### Requirement

ChronOS must help users renegotiate unrealistic commitments.

### Message Types

- extension request
- partial delivery note
- reschedule request
- delay apology
- delegation request
- follow-up reminder

### Acceptance Criteria

- Message is generated from commitment context.
- Message includes revised timeline and clear ask.
- User edits/copies manually.
- ChronOS does not send external messages without explicit user action.

---

## 5.14 Reflection Engine

### Requirement

ChronOS captures plan-vs-reality feedback.

### Fields

- planned duration
- actual duration
- completion status
- quality confidence
- energy level
- interruption count
- blocker reason
- notes

### Acceptance Criteria

- User can close a focus block with reflection.
- Reflection updates user memory.
- Future estimates reference historical patterns.
- Daily Review shows learned patterns.

---

## 5.15 Agent Trace Panel

### Requirement

ChronOS must show explainable agent activity.

### Trace Events

- input parsed
- commitment classified
- calendar fetched
- risk calculated
- plan generated
- drift detected
- replan proposed
- calendar write requested
- rescue activated
- reflection logged

### Acceptance Criteria

- Every major AI/tool action creates a trace event.
- Trace includes timestamp, step, tool, status, and explanation.
- Failed tool calls are visible.
- Trace does not expose private chain-of-thought.

---

## 6. Agentic Requirements

## 6.1 LangGraph Orchestration

ChronOS should use LangGraph for agent workflows.

Required nodes:

- intake
- classify
- clarify
- calendar_context
- risk_score
- time_spine_plan
- conflict_detection
- replan
- rescue
- negotiate
- reflect
- persist
- explain

## 6.2 State Persistence

Agent state should be checkpointed for:

- debugging
- continuing sessions
- inspecting actions
- recovering from failures
- generating trace logs

## 6.3 Human-in-the-Loop

Human approval required for:

- writing to Google Calendar
- moving hard-deadline focus blocks
- deleting commitments
- generating external communication for copying
- updating long-term user memory

---

## 7. Non-Functional Requirements

### 7.1 Performance

- Dashboard should load quickly.
- AI calls must show progress states.
- Agent runs should expose step progress.
- Calendar sync should not block the whole UI.

### 7.2 Reliability

- Backend validates all AI outputs.
- Pydantic schemas reject malformed responses.
- Failed AI calls do not corrupt state.
- Calendar write failures roll back internal pending state.

### 7.3 Security

- API keys server-side only.
- Supabase RLS enabled on user tables.
- Calendar tokens stored securely.
- Service role key never exposed to frontend.
- External writes require approval.

### 7.4 Privacy

- Store only productivity-relevant memory.
- Allow deletion of commitments/reflections.
- Minimize calendar details sent to AI prompts.
- Avoid unnecessary personal inferences.

### 7.5 Accessibility

- Keyboard-navigable core flows.
- Strong contrast.
- Visible focus states.
- Reduced motion option.
- Risk not communicated by color alone.

---

## 8. Data Model

### 8.1 `user_profiles`

- id
- user_id
- display_name
- timezone
- working_hours_json
- focus_preferences_json
- autonomy_level
- created_at
- updated_at

### 8.2 `commitments`

- id
- user_id
- title
- description
- type
- status
- deadline_at
- start_before_at
- estimated_minutes
- actual_minutes
- importance
- consequence
- flexibility
- progress_percent
- risk_level
- risk_score
- confidence_score
- created_at
- updated_at

### 8.3 `tasks`

- id
- commitment_id
- user_id
- title
- next_action
- done_condition
- estimated_minutes
- actual_minutes
- status
- sequence_order
- created_at
- updated_at

### 8.4 `time_spines`

- id
- commitment_id
- user_id
- spine_json
- current_stage
- created_at
- updated_at

### 8.5 `calendar_events`

- id
- user_id
- google_event_id
- title
- start_at
- end_at
- source
- is_chronos_created
- created_at
- updated_at

### 8.6 `focus_blocks`

- id
- user_id
- commitment_id
- title
- start_at
- end_at
- block_type
- status
- google_event_id
- created_at
- updated_at

### 8.7 `drift_events`

- id
- user_id
- commitment_id
- focus_block_id
- drift_type
- severity
- description
- created_at

### 8.8 `agent_runs`

- id
- user_id
- run_type
- status
- input_json
- output_json
- error_message
- created_at
- completed_at

### 8.9 `agent_trace_events`

- id
- agent_run_id
- user_id
- step_name
- tool_name
- status
- explanation
- payload_json
- created_at

### 8.10 `reflections`

- id
- user_id
- commitment_id
- focus_block_id
- planned_minutes
- actual_minutes
- completion_status
- energy_level
- blocker_reason
- quality_confidence
- notes
- created_at

### 8.11 `user_memory`

- id
- user_id
- memory_type
- key
- value_json
- confidence
- updated_at

---

## 9. API Contract

### 9.1 Auth

- `POST /auth/signup`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/session`

### 9.2 Commitments

- `GET /commitments`
- `POST /commitments`
- `GET /commitments/{id}`
- `PATCH /commitments/{id}`
- `DELETE /commitments/{id}`

### 9.3 Brain Dump

- `POST /ai/intake`

Request:

```json
{
  "raw_text": "string",
  "timezone": "Asia/Kolkata",
  "include_calendar_context": true
}
```

Response:

```json
{
  "commitments": [],
  "uncertain_items": [],
  "clarifying_questions": [],
  "agent_run_id": "uuid"
}
```

### 9.4 Time Spine

- `POST /ai/time-spine`
- `GET /commitments/{id}/time-spine`
- `PATCH /commitments/{id}/time-spine`

### 9.5 Risk

- `POST /risk/recalculate`
- `GET /risk/dashboard`

### 9.6 Calendar

- `GET /calendar/auth-url`
- `GET /calendar/callback`
- `GET /calendar/events`
- `POST /calendar/focus-blocks`
- `PATCH /calendar/focus-blocks/{id}`
- `DELETE /calendar/focus-blocks/{id}`

### 9.7 Agent Runs

- `POST /agent/run`
- `GET /agent/runs/{id}`
- `GET /agent/runs/{id}/trace`

### 9.8 Drift

- `POST /drift`
- `GET /drift/recent`
- `POST /agent/replan`

### 9.9 Rescue

- `POST /agent/rescue`
- `POST /agent/renegotiate`

### 9.10 Reflection

- `POST /reflection`
- `GET /reflection/daily`
- `GET /memory/patterns`

---

## 10. Recommended Stack

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Framer Motion
- React Flow or custom SVG canvas
- Zustand
- TanStack Query
- Zod

### Backend

- Python
- FastAPI
- LangGraph
- Pydantic
- Gemini API
- Google Calendar API
- Supabase client
- Uvicorn

### Database

- Supabase Auth
- Supabase Postgres
- RLS policies

### Deployment

- Google AI Studio / Google Cloud
- Cloud Run for backend
- environment variables for all secrets
- public deployed app link

---

## 11. First Public Release Requirements

Required:

- auth
- Supabase persistence
- Google Calendar integration
- brain dump extraction
- risk engine
- time spine
- command canvas
- drift logging
- replanner agent
- rescue mode
- negotiator
- reflection loop
- agent trace
- polished design
- demo scenarios
- README and submission doc

---

## 12. Submission Assets

Required for hackathon:

- public deployed app link
- GitHub repository
- Google Doc project description

Google Doc should contain:

- problem statement selected
- solution overview
- key features
- technologies used
- Google technologies utilized
- agentic architecture
- screenshots
- demo flow
- product philosophy
