# ChronOS — A secure AI Time Operating System for deadline recovery

Turn messy commitments into executable recovery paths with human-approved AI planning.

## Product overview
ChronOS is an AI-powered time operating system that takes messy, unstructured brain dumps and extracts structured commitments. It checks real calendar capacity and risk levels to proactively predict deadline collapse. ChronOS agents then propose schedule and rescue actions (like focus blocks or scope reduction) which require explicit human approval before execution, allowing you to regain control of your time through a continuous reflection loop.

## Problem statement
People don't only forget tasks; they lose control when commitments, deadlines, limited energy, and strict calendar realities conflict. Traditional task managers wait for you to fail, while autonomous agents make risky decisions without context. ChronOS acts as a "last-minute life saver," predicting deadline collapse before it happens and offering safe, executable recovery paths.

## Why ChronOS is different
* **Not a reminder app**: ChronOS orchestrates multi-stage focus and execution paths.
* **Not a chatbot**: ChronOS provides a structured, calm UI driven by deterministic capacity and risk rules.
* **Not an autonomous assistant**: ChronOS acts *only* with explicit human permission.
* **A Time Operating System**: It features planning, risk assessment, rescue generation, and human approval in one cohesive loop.

## Feature list
* **Brain Dump Intake**: Paste unstructured text to generate organized tasks.
* **Commitment Clarifier**: AI clarifies ambiguous intent and sets structured deadlines.
* **Time Health / Risk Engine**: Deterministic rules compare effort against calendar reality.
* **Google Calendar Read-Only Capacity**: Syncs real-world busy blocks to accurately find free focus time.
* **Schedule Proposal Agent**: LangGraph-based stateful agent proposing deep work blocks.
* **Rescue Mode**: Intervenes on failing commitments with scope compression, deadline renegotiation, or urgent recovery blocks.
* **Decision Dock**: A consolidated UI queue for human review of all AI proposals.
* **Daily Command Brief**: At-a-glance dashboard of Time Health and next best actions.
* **Reflection Loop**: Log actual effort after focus blocks to improve future risk modeling.
* **Supabase Auth + Google Login**: Secure account management.
* **Supabase Vault token security**: Google OAuth tokens are stored securely in Supabase Vault, inaccessible to the frontend.
* **About / Guide documentation**: In-product explanations of agentic behaviors.

## Architecture

```mermaid
flowchart LR
  User[User] --> FE[React + Vite Frontend]
  FE --> Auth[Supabase Auth]
  FE --> API[FastAPI Backend]
  API --> Gemini[Gemini API]
  API --> SG[LangGraph Scheduling Graph]
  API --> RG[LangGraph Rescue Graph]
  API --> DB[(Supabase Postgres + RLS)]
  API --> Vault[Supabase Vault]
  API --> GCal[Google Calendar Read-only API]
  SG --> DB
  RG --> DB
```

## Agentic workflow

```mermaid
flowchart TD
  Dump[Brain Dump] --> Extract[Extraction]
  Extract --> Review[Commitment Review]
  Review --> Risk[Risk Scoring]
  Risk --> Capacity[Calendar Capacity]
  Capacity --> Sched[Schedule Proposals]
  Capacity --> Resc[Rescue Proposals]
  Sched --> Dock[Decision Dock]
  Resc --> Dock
  Dock --> Approve[User Approval]
  Approve --> Focus[Focus Block / Reflection]
```

## Safety model
* **ChronOS proposes; user approves.**
* No focus blocks are created without explicit user approval.
* No external emails or messages are sent.
* Calendar integration is strictly read-only.
* OAuth tokens are stored server-side securely through Supabase Vault.
* The frontend never receives Google OAuth tokens or backend secrets.

## Google technologies
* **Gemini API**: Used for structured intent extraction and plan explanation.
* **Google Calendar**: Read-only API access for calculating focus capacity.
* **Google OAuth**: For secure calendar connection via user authorization.
* **Google Login**: Seamless authentication through Supabase OAuth provider.

## Tech stack

| Layer | Technologies |
|---|---|
| **Frontend** | React, TypeScript, Vite, Tailwind |
| **Backend** | FastAPI, Python, Pydantic |
| **AI / Agent** | Gemini, LangGraph |
| **Database/Auth** | Supabase Postgres, RLS, Supabase Auth, Supabase Vault |
| **Integrations** | Google Calendar API, Google OAuth |
| **Testing** | Pytest, Vite build / TypeScript |

## Local setup instructions

1. **Clone repo**: `git clone <repo_url> && cd chronos`
2. **Backend env vars**: Create `backend/.env` based on `backend/.env.example`. Do NOT commit this file.
3. **Frontend env vars**: Create `frontend/.env` based on `frontend/.env.example`. Do NOT commit this file.
4. **Supabase local start**: `supabase start --ignore-health-check` (Required due to local Logflare health quirks).
5. **Supabase db reset**: `supabase db reset` to apply schemas and seed Vault RPCs.
6. **Backend install/run**: 
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
7. **Frontend install/run**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
8. **Tests/Build commands**:
   ```bash
   # Backend
   cd backend && python -m pytest
   # Frontend
   cd frontend && npm run build
   ```

## Environment variables

### Backend
* `SUPABASE_URL`
* `SUPABASE_ANON_KEY`
* `SUPABASE_SERVICE_ROLE_KEY`
* `DEV_USER_ID` (Optional fallback for local bypass)
* `GEMINI_API_KEY`
* `GOOGLE_CLIENT_ID`
* `GOOGLE_CLIENT_SECRET`
* `GOOGLE_REDIRECT_URI`
* `GOOGLE_SCOPES`
* `FRONTEND_URL`

### Frontend
* `VITE_API_URL`
* `VITE_SUPABASE_URL`
* `VITE_SUPABASE_ANON_KEY`

> **WARNING**: Never commit `.env`, `backend/.env`, or `frontend/.env`.

## Auth setup notes
To use authentication locally or in production, configure your Supabase Dashboard:
* Enable **Email/Password** Auth.
* Enable **Confirm email** (Email Verification).
* Configure the **Google Provider** in Authentication -> Providers.
* Configure **Redirect URLs** (e.g., `http://localhost:5173/auth/callback` or production equivalent).
* Ensure the frontend uses the correct callback route to exchange OAuth hashes.

## Demo flow
1. Sign up or log in.
2. Open Command dashboard.
3. Scroll down and click **Load Judge Demo** from Connections & Demo Tools.
4. Click **Run ChronOS Analysis**.
5. Review the updated **Daily Command Brief** and Time Health.
6. Expand **Pending Approvals** to view proposed actions securely grouped by commitment.
7. Approve/reject a proposed action.
8. Review the Rescue, Focus, and Reflection flow in the Active Focus Console.

## Screenshots

> Add screenshots before final submission:
> - Landing
> - Command Brief
> - Decision Dock
> - Inbox
> - About/Guide

## Roadmap
* **Phase 7B**: Sprint Mode + First 15 Minutes + Starter Asset Generator
* **Phase 7D**: Drift/Avoidance Detector + Adaptive Replan
* **Phase 7E**: Final polish + deployment + submission packaging
* **Optional**: Gmail read-only commitment extraction

## Limitations
* Calendar integration is read-only.
* No autonomous calendar write-back.
* No external email sending capabilities.
* Mobile polish may need more targeted media queries.
* Gmail extraction is deferred to a future phase.

## Contribution status
Built for a hackathon submission, but strictly structured as a real product foundation with enterprise-grade security and RLS data isolation.
