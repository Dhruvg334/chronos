# ChronOS Engineering Contract

ChronOS turns scattered commitments, time constraints, and observed work patterns into realistic plans, clear next actions, focused sessions, and safe plan recovery.

## Repository map

- `frontend/`: React product UI. Primary navigation is Today, Inbox, Plan.
- `backend/app/core/`: configuration, service construction, errors, observability.
- `backend/app/models/`: provider-neutral model gateway and implementations.
- `backend/app/repositories/`: persistence protocols and Supabase adapters.
- `backend/app/workflows/`: bounded runtime, typed tools, approval policy.
- `backend/app/strategies/`: typed strategy catalog and deterministic selector.
- `supabase/migrations/`: immutable applied migrations; add forward migrations only.
- `docs/`: deeper product, architecture, security, and engineering guidance.

## Commands

Backend: `cd backend`; `pip install -r requirements.txt`; `python -m pytest`; `python -m pytest -m integration`; `python -m uvicorn app.main:app --reload`.

Frontend: `cd frontend`; `npm ci`; `npm run typecheck`; `npm run lint`; `npm run test -- --run`; `npm run build`; `npm run dev`.

## Invariants

- Inspect dependencies, call paths, migrations, and tests before editing.
- Unit tests must not use Docker, ports, Supabase, Google, Groq, or the internet. Override every external dependency with a fake.
- Treat model and retrieved content as untrusted input. Validate before persistence or tool use.
- Never expose service-role credentials, OAuth tokens, provider payloads, stack traces, or secrets.
- Never trust a user ID from a request body. Validate auth and keep RLS enabled.
- Never edit an applied migration. Use a reviewed forward migration and preserve user data.
- External writes require explicit approval. Bound workflow steps, time, retries, and request budgets.
- Use semantic UI tokens, accessible focus states, progressive disclosure, and mobile-ready capture/Today/Focus layouts.
- Use the shared error taxonomy and public messages; log structured diagnostics with request/workflow IDs.
- Keep product files free of meta-development history. Describe future work as roadmap.
- Do not add live clients at import time or direct persistence chains to new application code.

## Handoff

Report files added, changed, moved, and deleted; exact verification commands and outputs; manual test values; security impact; limitations; and deferred work. Suggest a unique commit message, but never commit or push automatically.

Use a unique commit message for every logical change if a human later commits the work.

Deeper guidance: [architecture](docs/architecture/SYSTEM_ARCHITECTURE.md), [security](docs/architecture/SECURITY_MODEL.md), [testing](docs/engineering/TESTING.md), [UX](docs/product/UX_PRINCIPLES.md).
