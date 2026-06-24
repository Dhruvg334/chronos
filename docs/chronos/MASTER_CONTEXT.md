# Chronos — Master Context Document

> Product name: **ChronOS**  
> Core idea: a proactive AI time operating system that manages commitments across their full journey, not a passive reminder app.  
> First public release context: Vibe2Ship / Google AI Studio hackathon.  
> Product ambition: real product in making, not a thin MVP.

---

## 1. Product Identity

### Name

**ChronOS**

- **Chron** references time.
- **OS** is visually differentiated to signal “Operating System.”
- The product should feel like a live operating layer for time, attention, commitments, and execution.

### Positioning

ChronOS is not a to-do list, calendar, habit tracker, Pomodoro timer, or chatbot wrapper.

ChronOS is an **adaptive commitment execution system** that:

1. captures messy commitments,
2. clarifies what action means,
3. maps work across time,
4. monitors reality drift,
5. replans dynamically,
6. rescues near-failing deadlines,
7. renegotiates unrealistic commitments,
8. learns how the user actually works.

### One-line pitch

**ChronOS converts messy commitments into adaptive time-spines, watches reality drift, and proactively replans your path from intention to completion.**

### Judge-facing pitch

Most productivity tools store tasks and send reminders. ChronOS assumes real life is messy. It captures commitments, connects to calendar reality, detects drift, and uses agentic AI to replan before deadlines break.

---

## 2. Hackathon Alignment

Selected problem statement: **Problem Statement 1 — The Last-Minute Life Saver**

The challenge asks for an AI-powered productivity companion that proactively assists users in planning, prioritizing, and completing tasks before deadlines are missed.

ChronOS goes beyond the literal prompt by treating missed deadlines as a **life-cycle execution failure**, not just a reminder failure.

### Evaluation matrix alignment

| Evaluation criterion | ChronOS response |
|---|---|
| Problem Solving & Impact | Focuses on missed deadlines, procrastination, overcommitment, time drift, and real execution failure |
| Agentic Depth | LangGraph orchestration, stateful planning, calendar tools, drift detection, replanning, rescue, negotiation |
| Innovation & Creativity | Time Spine, Drift Radar, Rescue Mode, Negotiator, Reflection Engine |
| Google Technologies | Gemini API, Google AI Studio, Google Cloud Run, Google Calendar API |
| Product Experience & Design | Warm light command-canvas UI, dynamic timeline, agent trace, interactive replanning |
| Technical Implementation | React/TypeScript frontend, FastAPI backend, Supabase, LangGraph, structured schemas |
| Completeness & Usability | End-to-end auth, persistence, calendar sync, agent runs, clear demo scenarios |

---

## 3. Core Thesis

People do not miss deadlines only because they forget. They miss deadlines because:

- they start too late,
- they underestimate effort,
- they do not define the next action,
- their calendar is already full,
- life events change the plan,
- they do not notice risk early,
- they fail to renegotiate before it is too late,
- they are overwhelmed by too many tasks,
- existing tools show lists but not viable execution paths.

ChronOS solves this by treating each commitment as a **time-bound execution journey**.

---

## 4. Product Philosophy

### 4.1 Time is not a list

Task lists hide capacity constraints. ChronOS represents work as **time-spines** and live execution paths.

### 4.2 Plans must survive reality

ChronOS assumes interruptions, overruns, low energy, meetings, dependency blocks, and scope changes are normal.

### 4.3 Productivity starts with clarification

A vague task is a procrastination trap. ChronOS compiles vague commitments into concrete next actions and done conditions.

### 4.4 Rescue is a first-class workflow

Falling behind is expected. ChronOS responds with minimum viable completion plans, scope cuts, compressed sprints, and renegotiation.

### 4.5 Human control matters

ChronOS may suggest, ask, or act depending on autonomy level and action risk. Calendar writes and external communications require explicit approval.

---

## 5. Scientific and Methodological Foundations

ChronOS should not be built on generic productivity clichés. It should operationalize established productivity, behavior-change, and planning principles.

### 5.1 GTD: Capture → Clarify → Organize → Reflect → Engage

ChronOS implementation:

- Brain Dump Inbox
- Commitment Clarifier
- Next Action Compiler
- Waiting-On Tracker
- Daily Review
- Action Selection Console

### 5.2 Implementation Intentions

Convert vague goals into if-then plans.

Example:

- Bad: “Work on project.”
- ChronOS: “If it is 7:30 PM and dinner is done, then open the repo and implement the `/agent/replan` schema for 45 minutes.”

ChronOS implementation:

- Action Contracts
- Start Cues
- Contextual triggers
- Done condition definition

### 5.3 Temporal Structure

Long-horizon work needs start-before dates, milestones, checkpoints, and buffers.

ChronOS implementation:

- Time Spine Engine
- Milestone Gates
- Feedback Gates
- Buffer Zones
- Start-Before Warnings
- Deadline Compression Detection

### 5.4 Deep Work

High-cognitive work needs protected blocks.

ChronOS implementation:

- Deep Work Blocks
- Focus Block Shield
- Material Checklist
- Distraction Risk Warnings
- Recovery Buffers
- Shallow Work Bundles

### 5.5 Early Feedback

Starting early is not enough. High-value tasks need intermediate review.

ChronOS implementation:

- Feedback Gates
- AI Draft Review
- Submission Readiness Scan
- Code/Resume/Assignment Checkpoint
- Quality Confidence Score

### 5.6 Planning Fallacy Correction

Humans underestimate effort. ChronOS must learn actual duration patterns.

ChronOS implementation:

- Reality Engine
- Estimate-vs-Actual Tracking
- Task-Type Overrun Factor
- Personal Buffer Calibration
- Future Estimate Adjustment

### 5.7 Habit Friction Design

ChronOS should avoid becoming a generic habit tracker. It should diagnose why habits fail.

ChronOS implementation:

- Habit Cue Designer
- Minimum Viable Habit
- Missed Habit Diagnosis
- Energy-Aware Rescheduling
- Friction Reduction Suggestions

---

## 6. Primary Users

### 6.1 Student Builder

A student managing classes, assignments, hackathons, interviews, coding projects, and personal goals.

Main pain points:

- deadline pileups,
- vague tasks,
- poor effort estimates,
- procrastination,
- competing academic/career priorities.

ChronOS value:

- time-spines for assignments/projects,
- rescue mode for deadlines,
- interview prep blocks,
- calendar-aware scheduling,
- reflection-based learning.

### 6.2 Early-Career Professional

A professional managing meetings, deliverables, follow-ups, bills, upskilling, and personal commitments.

Main pain points:

- scattered commitments,
- meeting overload,
- missed follow-ups,
- difficulty protecting deep work.

ChronOS value:

- calendar-aware capacity,
- follow-up tracking,
- focus block protection,
- renegotiation messages,
- day recovery after drift.

### 6.3 Founder / Operator

A builder managing product, sales, team, finance, personal life, and constant interruptions.

Main pain points:

- context switching,
- overloaded calendar,
- unclear tradeoffs,
- urgent work crowding important work.

ChronOS value:

- decision-oriented command canvas,
- risk-ranked commitments,
- weekly adaptive plan,
- explicit kill/defer/delegate layer.

---

## 7. Full Product Journey

ChronOS supports the entire commitment lifecycle.

### Stage 1 — Capture

User enters messy life input through text, voice, calendar import, or manual creation.

### Stage 2 — Clarify

ChronOS extracts:

- commitment type,
- deadline,
- effort estimate,
- progress,
- dependencies,
- next action,
- done condition,
- uncertainty,
- consequence,
- flexibility.

### Stage 3 — Model Reality

ChronOS builds a time model from:

- Google Calendar events,
- working hours,
- deep-work windows,
- energy preferences,
- existing focus blocks,
- user-defined unavailable time.

### Stage 4 — Build Time Spine

For significant commitments:

Capture → Clarify → Start → Milestone → Feedback → Buffer → Finalize → Submit → Reflect

### Stage 5 — Execute

The Command Canvas shows the current mission, why it matters now, the next action, and the done condition.

### Stage 6 — Monitor Drift

ChronOS detects:

- task overrun,
- underrun,
- skipped block,
- new event,
- low energy,
- scope expansion,
- dependency block,
- deadline change.

### Stage 7 — Replan

ChronOS recalculates the plan and explains:

- what changed,
- what moved,
- what got preserved,
- what became risky,
- what needs approval.

### Stage 8 — Rescue

When risk becomes critical:

- minimum viable completion path,
- must-do list,
- skip list,
- quality tradeoffs,
- compressed sprint,
- renegotiation option,
- final checklist.

### Stage 9 — Reflect

ChronOS learns from:

- planned vs actual duration,
- quality confidence,
- blockers,
- energy,
- interruptions,
- repeated estimate errors.

---

## 8. Product Modules

### 8.1 Brain Dump Inbox

Universal capture surface.

Input modes:

- text,
- bulk paste,
- voice,
- demo scenario loader,
- manual structured entry.

Output groups:

- hard deadlines,
- soft deadlines,
- events,
- habits,
- waiting-on items,
- quick actions,
- uncertain items,
- reference items.

### 8.2 Commitment Clarifier

Transforms messy input into actionable commitments.

Required fields:

- title,
- description,
- type,
- deadline,
- estimated effort,
- actual effort,
- progress,
- priority,
- consequence,
- flexibility,
- dependencies,
- next action,
- done condition,
- confidence.

### 8.3 Next Action Compiler

Every active commitment must have a concrete next action.

A next action includes:

- action statement,
- expected duration,
- context/materials,
- done condition,
- blocked condition,
- first 2-minute starter step.

### 8.4 Time Spine Engine

Generates visual execution paths with:

- start-before date,
- milestones,
- feedback gates,
- buffer zones,
- finalization window,
- deadline marker,
- reflection checkpoint.

### 8.5 Risk Engine

Scores commitment risk using:

- time remaining,
- effort remaining,
- free calendar capacity,
- progress,
- dependencies,
- energy fit,
- historical overrun factor,
- consequence,
- flexibility.

Risk levels:

1. Stable
2. Watch
3. At Risk
4. Critical
5. Rescue Required

### 8.6 ChronOS Command Canvas

Primary interface. Must not be a plain dashboard table.

Zones:

- Time Spine Panel
- Active Focus Console
- Agent Console
- Drift Radar
- Decision Dock
- Calendar Layer

### 8.7 Drift Radar

Logs and visualizes reality changes.

Drift types:

- time drift,
- event drift,
- energy drift,
- attention drift,
- scope drift,
- dependency drift,
- deadline drift.

### 8.8 Replanner Agent

Updates plans after drift.

Actions:

- move flexible work,
- protect hard deadlines,
- protect deep work,
- insert buffers,
- compress shallow work,
- defer low-impact tasks,
- trigger rescue,
- request approval.

### 8.9 Rescue Agent

Emergency execution planner.

Modes:

- 30-minute rescue,
- 90-minute rescue,
- tonight rescue,
- before tomorrow,
- submission sprint.

Outputs:

- minimum viable completion path,
- must-do sequence,
- skip list,
- quality risks,
- final checklist,
- renegotiation option.

### 8.10 Negotiator Agent

Generates messages for deadline or schedule renegotiation.

Types:

- extension request,
- partial delivery note,
- reschedule request,
- follow-up reminder,
- delegation message,
- apology + revised commitment.

### 8.11 Reflection Engine

Tracks actual work behavior.

Fields:

- planned minutes,
- actual minutes,
- completion status,
- energy level,
- blocker reason,
- interruption count,
- quality confidence,
- notes.

### 8.12 Google Calendar Layer

First-class feature, not optional.

Capabilities:

- Google OAuth,
- fetch events,
- detect free/busy windows,
- create ChronOS focus blocks,
- create rescue blocks,
- update ChronOS-created blocks,
- preserve approval for calendar writes.

### 8.13 Agent Trace Panel

Shows user-safe operational reasoning.

Trace should include:

- input parsed,
- fields extracted,
- calendar fetched,
- risk calculated,
- plan generated,
- drift detected,
- replan proposed,
- rescue activated,
- message drafted,
- calendar action requested.

Do not expose private chain-of-thought. Show structured action logs and explanations.

---

## 9. Agentic AI Architecture

ChronOS should use real agentic orchestration, preferably with LangGraph.

### 9.1 Agent Roles

- Capture Agent
- Clarifier Agent
- Calendar Agent
- Risk Agent
- Planner Agent
- Drift Agent
- Replanner Agent
- Rescue Agent
- Negotiator Agent
- Reflection Agent
- Explainer Agent

These should be implemented as graph nodes or well-structured modules, not as independent uncontrolled bots.

### 9.2 LangGraph Flow

Recommended graph:

1. Intake Node
2. Classification Node
3. Clarification Node
4. Calendar Context Node
5. Risk Scoring Node
6. Time Spine Planning Node
7. Conflict Detection Node
8. Replanning Node
9. Rescue Decision Node
10. Negotiation Node
11. Reflection Node
12. Persistence Node
13. Explanation Node

### 9.3 Graph State

State should include:

- user profile,
- user preferences,
- calendar context,
- commitments,
- tasks,
- events,
- free windows,
- focus blocks,
- risk scores,
- active plan,
- drift events,
- pending approvals,
- agent trace,
- reflection memory.

### 9.4 Tool Calls

Deterministic tools:

- `extract_commitments`
- `classify_commitment`
- `estimate_effort`
- `calculate_risk`
- `fetch_calendar_events`
- `find_free_windows`
- `generate_time_spine`
- `schedule_focus_block`
- `detect_drift`
- `replan_day`
- `generate_rescue_plan`
- `draft_renegotiation`
- `log_reflection`
- `update_user_memory`

### 9.5 Autonomy Levels

| Level | Name | Behavior |
|---|---|---|
| 1 | Suggest | Recommend only |
| 2 | Ask | Ask before applying |
| 3 | Act low-risk | Auto-apply low-risk changes |
| 4 | Rescue intervention | Forcefully surface rescue plan |
| 5 | External write | Calendar/write actions require explicit approval |

---

## 10. Preferred Technical Architecture

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Framer Motion
- React Flow or custom SVG canvas/timeline
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
- structured logging

### Database

- Supabase Auth
- Supabase Postgres
- Row Level Security
- user-scoped data
- optional Supabase Storage

### Google stack

- Google AI Studio
- Gemini API
- Google Calendar API
- Google Cloud Run
- OAuth consent flow
- optional Secret Manager
- optional Cloud Logging

---

## 11. Non-Negotiables

ChronOS must not become:

- a basic to-do app,
- a simple deadline table,
- a chatbot beside a dashboard,
- a static calendar view,
- a habit tracker clone,
- a generic Kanban board,
- an AI wrapper over reminders.

ChronOS must clearly demonstrate:

- stateful agent planning,
- Google Calendar awareness,
- deadline-risk modeling,
- adaptive replanning,
- proactive drift detection,
- rescue planning,
- human-in-the-loop control,
- full journey from capture to reflection.

---

## 12. Signature Demo Moment

The strongest demo should show this:

1. User brain-dumps a messy week.
2. ChronOS extracts commitments and calendar constraints.
3. It builds time-spines and scores risk.
4. User logs drift: “Backend integration took 75 minutes longer than planned.”
5. ChronOS recalculates risk.
6. The Time Spine visibly changes.
7. ChronOS preserves the hard deadline, moves low-priority work, proposes a Google Calendar update, and explains the tradeoff.
8. User accepts.
9. A critical task enters Rescue Mode.
10. ChronOS generates a minimum viable completion path and renegotiation message.

This interaction is ChronOS. Everything else supports it.
