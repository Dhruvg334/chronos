# Testing

Default tests are offline. They must not open sockets, local ports, Docker, Supabase, Google, or Groq. Repository, auth, model, and browser-network boundaries use deterministic fakes.

Backend:

```powershell
cd backend
.\venv\Scripts\activate
python -m pytest
python -m pytest -m integration
```

Runtime tests cover step and request budgets, timeouts, unknown tools, argument/result validation, read execution, internal/external write approval, model selection, idempotency metadata, and trace persistence on success and failure. Core journey tests cover consolidated Today, Strategy Engine cases, Plan composition/conflicts, Focus lifecycle, intake approval, recovery, and reflection.

Frontend:

```powershell
cd frontend
npm ci
npm run typecheck
npm run lint
npm run test -- --run
npm run build
```

Frontend tests cover consolidated Today, focus start/pause/resume/finish, stuck options, contextual reflection and recovery, plan-block success/conflict, strategy evidence, logout cache clearing, protected routes, and lazy route fallback.

Manual core profile: capture the documented multi-commitment sample, approve reviewed drafts, create a 60-minute authentication-fix block tomorrow at 10:00, repeat it to verify the overlap error, then run a 25-minute focus session through pause, resume, stuck, and partial reflection.
