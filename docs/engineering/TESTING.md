# Testing

Default tests are offline. They must not open sockets, local ports, Docker, Supabase, Google, or Groq. Repository, auth, model, and browser-network boundaries use deterministic fakes.

Backend:

```powershell
cd backend
.\venv\Scripts\activate
python -m pytest
python -m pytest -m integration
```

Runtime tests cover step and request budgets, timeouts, unknown tools, argument/result validation, read execution, internal/external write approval, model selection, idempotency metadata, and trace persistence. Core tests cover Today, Strategy Engine cases, profile capacity, Plan, Focus, intake, recovery, reflection, settings validation, and injected transaction rollback.

Integration tests are opt-in. Set `RUN_SUPABASE_INTEGRATION=1`, `SUPABASE_TEST_URL`, `SUPABASE_TEST_ANON_KEY`, and `SUPABASE_TEST_SERVICE_ROLE_KEY` from a disposable local stack. Without them, integration tests skip clearly. Live tests provision `chronos.alpha@example.com` and `chronos.beta@example.com`, exercise the core journey, and verify direct-JWT and backend ownership boundaries.

Set `RUN_GROQ_INTEGRATION=1` with `GROQ_API_KEY`, `GROQ_MODEL_FAST`, and `GROQ_MODEL_REASONING` to run the real structured-intake case. Set `RUN_GOOGLE_INTEGRATION=1` with backend Google credentials, `GOOGLE_OAUTH_STATE_SECRET`, `GOOGLE_TEST_USER_ID`, and disposable local Supabase configuration to validate a pre-authorized Vault-backed read-only connection, refresh, sync, and free/busy path. These tests never run by default.

Provider unit fixtures cover one repair, invalid structured output, timeouts, retryable server errors, rate limiting, provider unavailability, expired Google tokens, revoked refresh, timezone-preserving event sync, and token redaction. `python -m evals.run` reports the six small deterministic golden sets; the metrics describe fixture compliance only, not production quality.

Frontend:

```powershell
cd frontend
npm ci
npm run typecheck
npm run lint
npm run test -- --run
npm run build
```

Frontend tests cover Today, Focus, contextual reflection/recovery, plan success/conflict/transaction failure, adaptive proposal approval, explanation transparency, capacity and overload, profile-only degradation, personal availability validation/persistence, timezone rendering, schema incompatibility, logout cache clearing, protected routes, and lazy route fallback.

Manual profile: use `Asia/Kolkata`, Monday–Saturday, 09:30–18:30, 300 focus minutes, 45 default focus minutes, 10 transition minutes, 60 unscheduled minutes, lunch 13:00–14:00, and a 5-minute quick-task threshold. Confirm meetings, lunch, and transitions cannot overlap before running focus and recovery.
