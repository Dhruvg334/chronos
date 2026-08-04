<div align="center">

# ChronOS

### Adaptive planning, focused execution, and approval-based recovery

ChronOS turns commitments, projects, routines, calendar constraints, and working preferences into realistic daily and weekly plans.

</div>

## Overview

ChronOS is a full-stack personal execution system for knowledge workers and advanced students. It combines structured planning with bounded AI workflows, deterministic feasibility checks, secure persistence, attributable memory, read-first integrations, and explicit user approval before consequential changes.

The product is organized around a simple loop:

1. **Capture** work and context in Inbox.
2. **Decide** what is realistic in Today and Plan.
3. **Organize** meaningful work through Projects, Outcomes, Routines, and Week.
4. **Execute** with focused sessions and progress-aware reflection.
5. **Recover** when interruptions, overload, ambiguity, dependencies, or calendar changes invalidate the plan.
6. **Learn carefully** from confirmed preferences, reflections, notes, and prior choices without silently converting inference into fact.

ChronOS is recommendation-first. AI can extract intent, propose candidate plans, explain trade-offs, retrieve relevant context, and suggest recovery options. Ownership, time feasibility, overlap, protected intervals, capacity, dependencies, permissions, and persistence remain deterministic.

## Product capabilities

### Daily and weekly execution

- Natural-language Inbox capture with review before persistence
- Capacity-aware Today and Plan views
- Daily and weekly planning with protected time, buffers, calendar events, and focus limits
- Projects, completed-state Outcomes, executable commitments, and recurring Routines
- Focus sessions with start, pause, resume, completion, stuck guidance, and reflection
- Contextual recovery for overload, interruption, ambiguity, blocked dependencies, underestimation, low energy, and calendar disruption

### Personalization and context

- Three-step onboarding with resumable setup
- Availability, timezone, focus duration, transition, buffer, and planning-style preferences
- Explicit and inferred memory with confirmation, conflict review, provenance, expiry, and export
- Text, Markdown, project-context, and text-based PDF ingestion
- Hybrid lexical and vector retrieval with citations and ownership filtering
- Bounded context packs for planning, recovery, projects, reflection, and stuck guidance

### Integrations and interoperability

- Read-only Google Calendar synchronization and free/busy context
- Read-first connector contracts for Gmail, GitHub, Notion, Outlook Calendar, Obsidian imports, and Microsoft Planner
- External Inbox proposals that require review before becoming ChronOS work
- Scoped MCP server and client foundations with allow-listing, typed permissions, budgets, validation, and audit trails
- No unrestricted remote execution and no external write executor

### Reliability and control

- Supabase Auth, PostgreSQL, RLS, Vault-backed token handling, and composite ownership constraints
- Atomic PostgreSQL transactions for approval and multi-write workflows
- Idempotency, rollback, quota enforcement, retention, export, and account deletion controls
- Provider-neutral model and embedding gateways
- Bounded workflow steps, request budgets, retries, repair attempts, and timeouts
- Shared failure taxonomy, prompt/model versioning, structured traces, and safe health endpoints
- Versioned evaluation datasets and deterministic regression metrics

## Architecture

```text
Browser
  React + TypeScript + Vite + TanStack Query
            │
            │ authenticated HTTPS API
            ▼
FastAPI application
  APIs · services · bounded workflows · deterministic validators
  provider-neutral model, embedding, integration, and MCP boundaries
            │
            ├── Groq generation gateway
            ├── Embedding gateway
            ├── Read-first provider connectors
            └── Supabase repositories
                        │
                        ▼
Supabase
  PostgreSQL · Auth · RLS · pgvector · Vault · transactional RPCs
```

### Repository map

| Path | Responsibility |
|---|---|
| `frontend/` | React application, protected routes, product surfaces, accessibility, and client-side server-state management |
| `backend/app/api/` | Typed FastAPI endpoints and authenticated product contracts |
| `backend/app/services/` | Planning, context, lifecycle, readiness, and domain services |
| `backend/app/workflows/` | Bounded intake, planning, recovery, approval, and tool workflows |
| `backend/app/repositories/` | Persistence protocols, Supabase adapters, and test fakes |
| `backend/app/models/` | Provider-neutral model gateway and Groq implementation |
| `backend/app/embeddings/` | Embedding contract, offline fallback, and semantic provider implementation |
| `backend/app/integrations/` | Connector contracts, adapters, normalization, synchronization, and audit behavior |
| `backend/app/mcp/` | Scoped MCP server and client foundations |
| `supabase/migrations/` | Append-only schema, RLS, grants, indexes, pgvector, Vault, and transactional functions |
| `docs/` | Product, architecture, security, evaluation, operations, testing, and deployment documentation |
| `scratch/` | Ignored local experiments; never a place for credentials or application code |

## Technology

### Frontend

- React 19
- TypeScript
- Vite
- Tailwind CSS
- TanStack Query
- Supabase browser authentication
- Vitest and Testing Library

### Backend

- Python 3.12
- FastAPI
- Pydantic
- Supabase Python client
- Groq through an OpenAI-compatible provider gateway
- Google Calendar API
- `pypdf` for text-based PDF extraction
- Pytest

### Data and infrastructure

- Supabase PostgreSQL
- Row Level Security
- pgvector
- Supabase Vault
- Netlify-compatible frontend configuration
- Stateless FastAPI deployment configuration for Render or Koyeb

## Local development

### Prerequisites

- Python 3.12
- Node.js 22
- npm
- Docker Desktop
- Supabase CLI

### 1. Clone and configure

```powershell
git clone <repository-url>
cd chronos
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

Populate the local Supabase values after starting the stack. Keep all service-role, model-provider, OAuth, encryption, and integration secrets in `backend/.env` only.

### 2. Start Supabase

```powershell
supabase start --ignore-health-check
supabase status
```

The repository uses local ports `55321`–`55324`. Copy the local API URL, publishable/anon key, and service-role key into the corresponding backend and frontend environment files.

Apply all migrations on a new local database:

```powershell
supabase db reset
supabase migration list --local
```

### 3. Start the backend

Install dependencies only when the environment is first created or when dependency manifests change.

```powershell
cd backend
py -3.12 -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

Backend: `http://127.0.0.1:8000`  
Liveness: `http://127.0.0.1:8000/api/v1/health/live`  
Readiness: `http://127.0.0.1:8000/api/v1/health/ready`

### 4. Start the frontend

Install dependencies only on first setup or after `package.json` or the lockfile changes.

```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://127.0.0.1:5173`

## Environment boundaries

### Frontend variables

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_SUPABASE_URL=http://127.0.0.1:55321
VITE_SUPABASE_ANON_KEY=...
```

These values are public browser configuration.

### Backend-only variables

The backend owns:

- `SUPABASE_SERVICE_ROLE_KEY`
- `GROQ_API_KEY`
- embedding-provider credentials
- Google and other OAuth client secrets
- `GOOGLE_OAUTH_STATE_SECRET`
- `ENCRYPTION_KEY`
- integration and MCP allow-lists
- CORS, host, quota, retry, timeout, and workflow-budget configuration

See [`backend/.env.example`](backend/.env.example) for the complete contract.

## Verification

### Backend

```powershell
cd backend
.\venv\Scripts\activate
python -m pytest
pip check
```

Live integration suites are opt-in and require explicit disposable local credentials. They do not run during the default suite.

### Frontend

```powershell
cd frontend
npm run typecheck
npm run lint
npm run test -- --run
npm run build
```

### Database

```powershell
supabase status
supabase migration list --local
```

Run `supabase db reset` only when validating migrations or rebuilding disposable local data.

## Security model

ChronOS assumes that model output, retrieved documents, emails, integration payloads, and MCP responses are untrusted.

Key controls include:

- authenticated identity derived from Supabase tokens rather than request payloads;
- RLS and explicit user scoping for all owned records;
- service-role-only chunk, vector, token, quota, and lifecycle operations where required;
- restricted `SECURITY DEFINER` search paths and narrow grants;
- explicit approval before internal plan mutations and all external writes;
- safe source attribution without exposing embeddings, raw provider payloads, or hidden reasoning;
- bounded file sizes, pagination, requests, retries, workflow steps, and provider usage;
- redacted logs and public errors with correlation IDs;
- user-controlled export, source deletion, connection revocation, and account deletion.

See [`docs/architecture/SECURITY_MODEL.md`](docs/architecture/SECURITY_MODEL.md).

## Deployment

The repository is prepared for a split deployment:

- **Frontend:** Netlify
- **Backend:** Render or Koyeb-compatible Python web service
- **Database, authentication, Vault, and vectors:** hosted Supabase
- **Generation:** Groq
- **Embeddings:** configured semantic provider, with deterministic local fallback for offline development

Deployment configuration and environment guidance are documented in [`docs/engineering/DEPLOYMENT.md`](docs/engineering/DEPLOYMENT.md).

## Documentation

### Product

- [Product strategy](docs/product/PRODUCT_STRATEGY.md)
- [Strategy Engine](docs/product/STRATEGY_ENGINE.md)
- [UX principles](docs/product/UX_PRINCIPLES.md)

### Architecture and security

- [System architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)
- [Agent runtime](docs/architecture/AGENT_RUNTIME.md)
- [Context and memory](docs/architecture/CONTEXT_MEMORY.md)
- [Integration model](docs/architecture/INTEGRATION_MODEL.md)
- [Security model](docs/architecture/SECURITY_MODEL.md)

### Engineering and operations

- [Development](docs/engineering/DEVELOPMENT.md)
- [Testing](docs/engineering/TESTING.md)
- [Evaluation system](docs/engineering/EVALUATION_SYSTEM.md)
- [Observability](docs/engineering/OBSERVABILITY.md)
- [Operations and recovery](docs/engineering/OPERATIONS.md)
- [Deployment](docs/engineering/DEPLOYMENT.md)
- [Roadmap](docs/ROADMAP.md)

## Engineering principles

- Deterministic feasibility outranks model preference.
- User approval outranks automation convenience.
- Explicit memory outranks inferred memory.
- Provenance outranks unsupported summarization.
- Cached and structured data keep the product usable during provider failure.
- Applied migrations remain immutable; changes move forward.
- Tests use fakes by default and opt into live systems explicitly.
- Product surfaces remain quiet, contextual, and progressively disclosed.

Before changing the repository, read [`AGENTS.md`](AGENTS.md).
