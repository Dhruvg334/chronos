# ChronOS — Proactive AI Time Operating System

> **"Your time does not need another list. It needs an operating system."**

ChronOS is an adaptive commitment execution system that converts messy life inputs into structured execution paths (Time Spines), maps work against calendar reality, detects planning deviations (Drift), and leverages agentic AI to replan or rescue commitments before deadlines fail.

---

## 1. Product Philosophy & Thesis

Most productivity tools store tasks and send static notifications. ChronOS assumes real life is messy and plans rarely survive contact with reality. Users miss deadlines not because they forget, but because:
1. They start too late and underestimate effort.
2. Vague tasks act as procrastination traps.
3. Their calendars are full of unrecognized blocks.
4. They fail to renegotiate or cut scope until it is too late.

ChronOS solves this by operationalizing **GTD**, **Implementation Intentions**, **Planning Fallacy corrections**, and **proactive rescue workflows** into a single cohesive interface.

---

## 2. System Architecture

ChronOS is constructed as a monorepo consisting of:
- **Frontend**: A React + TypeScript + Vite app styled with a premium warm light palette, featuring an interactive SVG Time Spine, Active Focus timer, real-time Agent Trace viewer, and a Decision Dock approval console.
- **Backend**: A FastAPI server running Python-based business modules and six dedicated **LangGraph** agent graphs.
- **Database**: A Supabase PostgreSQL database utilizing Row Level Security (RLS) and automated triggers for user onboarding and metadata updates.

```text
  ┌─────────────────────────────────────────────────────────────┐
  │                        React Frontend                       │
  │   (Command Canvas, Time Spine, Decision Dock, Agent Trace)   │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                        HTTP REST / SSE / JWT
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                        FastAPI Server                       │
  │     [API Routers] ───> [LangGraph Multi-Mode Graphs]        │
  └──────────────┬───────────────────────────────┬──────────────┘
                 │                               │
             Postgres / RLS                  Gemini API / Calendar API
                 │                               │
                 ▼                               ▼
  ┌──────────────────────────────┐ ┌────────────────────────────┐
  │      Supabase Database       │ │      Google Services       │
  │   (RLS Onboard & Triggers)   │ │  (AI Studio, OAuth, Cal)   │
  └──────────────────────────────┘ └────────────────────────────┘
```

---

## 3. Directory Structure

```text
chronos/
├── docs/                      # Product specs and ADRs
│   ├── chronos/
│   │   ├── MASTER_CONTEXT.md
│   │   ├── PROJECT_REQUIREMENTS.md
│   │   ├── DESIGN_SPECIFICATIONS.md
│   │   ├── ARCHITECTURE_DECISIONS.md # ADRs (auth, connections, agents)
│   │   ├── BUILD_STATUS.md           # Live feature tracking checklist
│   │   └── IMPLEMENTATION_PLAN.md    # Multi-phase implementation roadmap
│   └── skills/
│       └── SKILLS_RECOMMENDATIONS.md # Recommended tooling integrations
├── supabase/                  # Supabase schema definitions and migration SQLs
├── backend/                   # FastAPI + LangGraph server
│   ├── app/
│   │   ├── api/               # Router endpoints (auth, commitments, calendar, drift, agent)
│   │   ├── core/              # Config, security, DB connections
│   │   ├── schemas/           # Pydantic validation models
│   │   ├── services/          # Calendar sync, risk algorithms, database helpers
│   │   └── agents/            # LangGraph graph modules and LLM tools
│   ├── tests/                 # Unit and integration test suite
│   ├── requirements.txt       # Dependencies list
│   └── .env.example           # Secrets template
└── frontend/                  # React + TypeScript + Vite app
    ├── src/
    │   ├── components/        # Canvas widgets (TimeSpine, FocusConsole, AgentTrace)
    │   ├── store/             # Zustand states (auth, canvas, agent runs)
    │   └── pages/             # Layout sheets (Landing, Canvas, Inbox, Rescue)
    └── package.json
```

---

## 4. Google Technologies Utilized

1. **Google AI Studio & Gemini API**: Powers structured extraction, task complexity classification, replanning calculations, rescue plans, and communication scripts.
2. **Google Calendar API**: Pulls events, calculates active capacity slots, and creates/reschedules focus blocks.
3. **Google Cloud Run**: Hosts the FastAPI backend container for production.

---

## 5. Setup & Local Development

### 5.1 Supabase Setup
1. Create a Supabase project.
2. Run the SQL files in `supabase/migrations/` in chronological order to initialize tables, constraints, RLS policies, and triggers.

### 5.2 Backend Installation
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and install dependencies:
## Status: Phase 2 Completed
- **Phase 1**: Database setup (Supabase migrations, RLS, triggers).
- **Phase 2**: AI Intake Loop, Brain Dump Extraction with Gemini, Risk Scoring, and Command Canvas initialization.

### Phase 2 Local Runbook

**1. Database Configuration**
```bash
# Start local Supabase (ignores known analytics container issue)
npx supabase start --ignore-health-check
```
*Run `npx supabase status` and copy `API URL`, `anon key`, and `service_role key`.*

**2. Environment Configuration**
* Copy `.env.example` to `.env` in the root folder.
* Copy `backend/.env.example` to `backend/.env`.
* Fill in `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` (backend only), and `GEMINI_API_KEY` (backend only).
* Set `DEV_USER_ID` in `backend/.env` using a UUID from `docs/chronos/DB_VERIFICATION.md` for Dev Auth bypass.

**3. Start Backend & Tests**
```bash
cd backend
python -m venv venv
venv\Scripts\activate # Windows
pip install -r requirements.txt
python -m pytest
python -m uvicorn app.main:app --reload
```

**4. Start Frontend**
```bash
# Open a new terminal
cd frontend
npm install
npm run build
npm run dev
```

**5. Manual Test Flow**
1. Open `http://localhost:5173/inbox`.
2. Click the "Hackathon Week" quick prompt and submit.
3. Review the AI-extracted commitment drafts and observe the trace logs in the Agent Console.
4. Approve the commitments.
5. Navigate to `http://localhost:5173/command` to view your saved commitments, risk levels, and basic time spines.

---

## 6. Signature Demo Scenarios

ChronOS provides four first-class interactive scenarios to demonstrate its capabilities:

### Scenario A: Hackathon Week (The Core Loop Demo)
1. **Intake**: Paste a messy paragraph: *"Need to build the landing page by Friday, write API tests by Wednesday, and present the demo on Saturday. I also have classes from 10 AM to 2 PM daily."*
2. **Spine Creation**: Gemini extracts these tasks, maps milestone checkpoints, and builds the SVG Time Spine, overlaying daily class schedules.
3. **Drift**: Log a drift event: *"Frontend landing design took 2 hours longer than planned."*
4. **Replan**: The Replanner agent detects a meeting collision. It shifts low-priority tasks, creates a focus block suggestion in the Decision Dock, and streams server-side trace details in the Agent Console.
5. **Approval**: Clicking "Approve" moves the calendar events.

### Scenario B: Assignment Crisis (Rescue Mode Demo)
1. **Critical Drift**: Log: *"I haven't started my university project, and it is due in 6 hours."*
2. **Rescue Trigger**: The Risk Engine flags the commitment status as `Rescue Required` (load ratio > 100%).
3. **MVCP Output**: The screen shifts to a Rescue border. ChronOS provides a Minimum Viable Completion Path: strips non-essential research steps, locks a 3-hour deep work block, and disables distracting tabs.
4. **Negotiation**: The Negotiator agent drafts a polite extension request template.

### Scenario C: Interview Prep Week (Long-Horizon Planning)
1. **Milestones**: A 2-week prep timeline is segmented into milestones (Algorithms study, System Design mock, Resume review).
2. **Feedback Gates**: Inserts review checkpoints (e.g. feedback from resume review) 3 days before submission.

### Scenario D: Busy Professional Day (Context-Aware Shielding)
1. **Deep Work Protection**: Auto-reschedules focus blocks around urgent client calls while maintaining task deadlines.
