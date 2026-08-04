# Testing

Default tests are offline. They must not open sockets, local ports, Docker, Supabase, Google, or Groq. Repository, auth, model, and browser-network boundaries use deterministic fakes.

Backend:

```powershell
cd backend
.\venv\Scripts\activate
python -m pytest
python -m pytest -m integration
```

Runtime tests cover step and request budgets, timeouts, unknown tools, argument/result validation, read execution, internal/external write approval, model selection, idempotency metadata, and trace persistence. Core tests cover Today, Strategy Engine cases, profile capacity, Plan, Focus, intake, recovery, reflection, settings validation, projects, outcome linking, routine scheduling/continuity, weekly capacity/proposal validation, approval, ownership, and injected transaction rollback.

Focused personalization tests cover onboarding save/resume/skip/completion, preference-driven strategy and explanation behavior, focus-duration options, deterministic stuck guidance, recovery dismissal/approval boundaries, concise feedback redaction, and feedback RLS ownership.

Focused context tests cover explicit and proposed memory, sensitive-inference rejection, contradiction review, correction history, duplicate ingestion, text/file validation, prompt-injection text, embedding failure, hybrid ranking, ownership filtering, context-pack budgets, retrieval fallback, reflection proposals, citations, ingestion rollback, and browser denial of chunk/vector access. `python -m evals.context_run` reports synthetic fixture metrics for 10 documents, 12 queries, 8 memory cases, 6 duplicate cases, and 6 context-pack cases; these are regression signals, not production-quality claims.

Integration tests are opt-in. Set `RUN_SUPABASE_INTEGRATION=1`, `SUPABASE_TEST_URL`, `SUPABASE_TEST_ANON_KEY`, and `SUPABASE_TEST_SERVICE_ROLE_KEY` from a disposable local stack. Without them, integration tests skip clearly. Live tests provision `chronos.alpha@example.com` and `chronos.beta@example.com`, exercise the core journey, and verify direct-JWT and backend ownership boundaries.

Set `RUN_GROQ_INTEGRATION=1` with Groq settings in `backend/.env` to run live structured intake, adaptive-plan validation, bounded recovery, provider metadata, and redaction/error-classification checks. The opt-in flag must still be present in the process environment. Set `RUN_GOOGLE_INTEGRATION=1` with backend Google credentials, `GOOGLE_OAUTH_STATE_SECRET`, `GOOGLE_TEST_USER_ID`, and disposable local Supabase configuration to validate a pre-authorized Vault-backed read-only connection, refresh, sync, and free/busy path. These tests never run by default.

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

Frontend tests cover Today, Focus, contextual reflection/recovery, plan success/conflict/transaction failure, adaptive proposal approval, explanation transparency, capacity and overload, profile-only degradation, personal availability validation/persistence, projects and outcomes, routines, weekly proposal accept/edit/reject, Inbox assignment, responsive navigation, timezone rendering, schema incompatibility, logout cache clearing, protected routes, and lazy route fallback.

Integration-focused offline tests cover normalized pagination/idempotency, provider failure/cached fallback, Google recurrence/cancellation/timezone handling, Gmail quote reduction and proposal signals, selected GitHub/Notion resources, Microsoft read contracts, Obsidian archive safety, MCP SSRF/schema/permission controls, and workflow permission enforcement. `tests/integration/test_integrations_supabase.py` is opt-in and verifies two-user RLS, column grants, cross-user mutation denial, proposal rollback, approval atomicity, and safe retry.

Manual profile: use `Asia/Kolkata`, Monday–Saturday, 09:30–18:30, 300 focus minutes, 45 default focus minutes, 10 transition minutes, 60 unscheduled minutes, lunch 13:00–14:00, and a 5-minute quick-task threshold. Confirm meetings, lunch, and transitions cannot overlap before running focus and recovery.
