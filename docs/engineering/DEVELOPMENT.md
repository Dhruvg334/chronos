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

Core API entry points are `GET /api/v1/today`, `POST /api/v1/today/strategy`, `GET /api/v1/plan`, `POST /api/v1/plan/blocks`, and `/api/v1/focus-blocks` lifecycle routes.
