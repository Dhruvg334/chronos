# ChronOS

ChronOS is an open-source personal planning, execution, and time system for knowledge workers and advanced students.

It turns scattered commitments into a realistic day and helps repair the plan when reality changes. The current product foundation includes authenticated capture, commitment planning, calendar read access, focus blocks, reflections, recommendation-first approvals, deterministic strategy selection, and bounded workflow infrastructure.

## Product loop

1. Capture commitments in **Inbox**.
2. Review the realistic next action in **Today**.
3. Shape time blocks and buffers in **Plan**.
4. Focus, reflect, and adjust with explicit approval for consequential changes.

The public `/demo` route uses static data and does not access protected APIs.

## Architecture

- `frontend/`: React, TypeScript, Vite, Tailwind, TanStack Query, Supabase Auth.
- `backend/`: FastAPI, Pydantic, repository protocols, Groq model gateway, bounded workflow runtime.
- `supabase/`: append-only database migrations, RLS policies, grants, and Vault-backed Google OAuth token handling.
- `docs/`: product, architecture, engineering, security, and roadmap documentation.
- `.codex/skills/`: repository-local engineering workflows.

Supabase is the database and authentication platform. Groq is the default model provider through a provider-neutral gateway. Google Calendar remains read-only. No external write integration is enabled.

## Quick start

Backend (PowerShell, Python 3.12):

```powershell
cd backend
py -3.12 -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest
python -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm ci
npm run typecheck
npm run lint
npm run test -- --run
npm run build
npm run dev
```

Copy `.env.example` values into environment-specific files and replace placeholders. The frontend receives only `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`. The service-role key and provider keys remain backend-only.

## Documentation

- [Product strategy](docs/product/PRODUCT_STRATEGY.md)
- [System architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)
- [Security model](docs/architecture/SECURITY_MODEL.md)
- [Development](docs/engineering/DEVELOPMENT.md)
- [Testing](docs/engineering/TESTING.md)
- [Roadmap](docs/ROADMAP.md)

See [AGENTS.md](AGENTS.md) before changing the repository.

## License

An open-source license has not yet been selected. Add one before distributing packaged releases.
