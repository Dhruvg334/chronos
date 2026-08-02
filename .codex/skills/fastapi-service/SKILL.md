---
name: fastapi-service
description: Implement or refactor ChronOS FastAPI endpoints, dependencies, application services, repositories, error responses, health checks, and offline tests. Use for backend API behavior or service-boundary work.
---

# FastAPI Service

## Required inputs

- Endpoint contract and authenticated actor
- Repository/model/integration dependencies
- Error and idempotency behavior
- Existing unit tests and callers

## Workflow

1. Inspect route, service, schema, repository protocol, and callers.
2. Obtain user identity from validated dependencies only.
3. Inject repositories/gateways; never create live clients in modules.
4. Validate inputs and provider output with Pydantic.
5. Raise the shared typed errors with safe public messages.
6. Override every external dependency in tests.

## Checks

- Default tests use no ports, network, Docker, Supabase, Google, or Groq.
- Responses contain no secrets, payload dumps, or traces.
- Request IDs and classified structured logs are preserved.
- Critical persistence failures remain visible.

## Commands

Run `cd backend`; `python -m pytest`; `python -m pytest -m integration`; import `app.main`; start Uvicorn for a bounded smoke check.

## Expected output

Return typed endpoint behavior, fake-backed tests, HTTP/error mapping, and exact verification.

## Stop conditions

Stop before trusting body-supplied identity, bypassing RLS, swallowing persistence errors, or embedding provider/model details in domain logic.
