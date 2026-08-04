# ChronOS backend

The backend is a FastAPI application that owns authenticated product APIs, deterministic planning, bounded model-assisted workflows, repositories, integrations, MCP permissions, operational controls, and user data lifecycle behavior.

## Environment

Copy `.env.example` to `.env`. Backend secrets must never be exposed through Vite variables or committed files.

## Commands

```powershell
py -3.12 -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pytest
python -m uvicorn app.main:app --reload
```

Install dependencies only on first setup or after dependency manifests change.

## API health

- `GET /api/v1/health/live`: dependency-free liveness
- `GET /api/v1/health/ready`: bounded public readiness
- Authenticated operational status is available through the operations API and exposes no secrets or account identifiers.

## Boundaries

- APIs depend on services and repository protocols rather than import-time provider clients.
- Model, retrieved, email, integration, and MCP content is untrusted.
- Deterministic validation and approval policy control persistence.
- Unit tests remain offline; live Supabase and provider tests are explicit opt-in suites.
- Applied migrations are immutable and security changes move forward.
