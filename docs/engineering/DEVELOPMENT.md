# Development

Use Python 3.12 and npm with the committed lockfile. Copy environment examples and replace placeholders locally; never commit secrets.

Backend PowerShell:

```powershell
cd backend
py -3.12 -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm ci
npm run dev
```

Before handoff, run every command in `TESTING.md`. Default tests must stay offline. Add application persistence through repository protocols, external clients through the lazy container, and schema changes through forward migrations only. Do not edit applied migrations.

Core API entry points are `GET /api/v1/today`, `POST /api/v1/today/strategy`, `GET /api/v1/plan`, `POST /api/v1/plan/blocks`, `POST /api/v1/plan/adaptive`, `POST /api/v1/plan/adaptive/{proposal_id}/approve`, and `/api/v1/focus-blocks` lifecycle routes.

Planning settings are at `/api/v1/settings/planning-profile`; integration state is at `/api/v1/settings/integrations`. ChronOS local Supabase ports are isolated in `supabase/config.toml` (API 55321, database 55322, Studio 55323).

Critical writes accept `Idempotency-Key`. Repository adapters call `approve_intake_transaction`, `complete_focus_transaction`, `approve_recovery_transaction`, and `approve_adaptive_plan_transaction`; do not replace them with sequential REST writes.

Provider integration commands are opt-in:

```powershell
$env:RUN_GROQ_INTEGRATION='1'    # requires backend-only Groq key and configured models
$env:RUN_GOOGLE_INTEGRATION='1'  # requires a disposable Vault-connected Google test user
python -m pytest -m integration -vv
python -m evals.run
```
