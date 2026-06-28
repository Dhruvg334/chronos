# Architecture Decisions

## 1. Google OAuth Delegation
Google Calendar OAuth is deferred to Phase 5. In early phases, a `mock_capacity_service` is used to estimate user available bandwidth for Time Spines and Risk Initialization.

## 2. Gemini Multi-Model Approach
Configured via `.env` to avoid hardcoding models.
`GEMINI_MODEL_FAST` (gemini-2.5-flash) is used for initial extraction.
`GEMINI_MODEL_REASONING` (gemini-2.5-pro) is triggered only during the 1-retry repair loop if Pydantic validation fails on the fast model's output.

## 3. Deterministic Risk Initialization
Risk is not AI-generated; it is deterministically calculated using an explicit equation taking into account effort remaining, time until deadline, importance, flexibility, and confidence.
`risk_score = clamp(raw_score * uncertainty_factor, 0, 100)`

## 4. Frontend Trace Polling
Frontend Agent Console uses simple HTTP polling to `GET /api/v1/agent/runs/{id}/trace` to fetch trace logs (e.g. `gemini_extraction_started`). SSE is deferred to later phases.

## 5. Temporary Dev Auth
Uses a lightweight dependency mock relying on `DEV_USER_ID` environment variable to link `user_id` context until Supabase JWT middleware is complete. This ensures `user_id` is never passed directly from the frontend request body.

## 6. Technical Debt
- **google.generativeai**: Currently using the legacy `google.generativeai` package instead of the newer `google-genai` SDK. This is a known technical debt item to be migrated in a future phase.
- **Trace Polling**: Agent trace polling currently uses simple HTTP `setInterval` instead of an active Server-Sent Events (SSE) stream.
