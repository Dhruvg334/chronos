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

Before a handoff, run every command in `TESTING.md`. Do not use unsafe dependency flags. Add external clients only through the application container and dependencies. Add database changes as forward migrations.
