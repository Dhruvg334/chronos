# Architecture Decisions

## 1. Google OAuth Delegation
Google Calendar OAuth is deferred to Phase 5. In early phases, a `mock_capacity_service` is used to estimate user available bandwidth for Time Spines and Risk Initialization.

## 2. Gemini Multi-Model Approach
Configured via `.env` to avoid hardcoding models.
`GEMINI_MODEL_FAST` (gemini-2.5-flash) is used for initial extraction.
`GEMINI_MODEL_REASONING` (gemini-2.5-pro) is triggered only during the 1-retry repair loop if Pydantic validation fails on the fast model's output.

### AD-006: Frontend Extensibility without Server-Side Rendering
- **Context**: Future plugins and dynamic UI.
- **Decision**: Vite + React single-page app (SPA). No Next.js or SSR is required, ensuring maximum speed for backend API iteration. All complex logic lives in FastAPI, not the UI. 

### AD-007: OAuth Token Storage & Security
- **Context**: Need to securely store Google Calendar OAuth tokens without leaking them in standard tables or frontend requests.
- **Decision**: Use Supabase Vault (`pgsodium` / `supabase_vault`). Store encrypted tokens in `vault.secrets` and only retain `access_token_secret_id` and `refresh_token_secret_id` inside `public.google_connections`.
- **Implementation**: Access to Vault is wrapped in `SECURITY DEFINER` RPC functions (`public.set_google_tokens`, `public.get_decrypted_google_tokens`).
- **Security Constraint**: These RPC functions have their execute permissions revoked from `public` and `authenticated`, and granted EXCLUSIVELY to `service_role`. The backend FastApi uses the Service Role key to fetch tokens securely in-memory. Tokens are strictly passed transiently to Google APIs and never logged or exposed in API JSON payloads.

### AD-008: LangGraph MVP and Human-In-The-Loop Scheduling
- **Context**: The Agent needs to propose schedule actions securely without hallucinating time slots or destructively overwriting external Google Calendars.
- **Decision**: LangGraph MVP (`scheduling_graph.py`) orchestrates deterministic generation of candidate focus blocks based on remaining effort, risk score, and valid capacity windows (from `capacity_service.py`).
- **Implementation**: Proposals are saved to `agent_proposed_actions`. A `DecisionDock` in the frontend surfaces these proposals. Only when the user hits "Approve" is the time slot validated against overlapping constraints again before being persisted as an internal ChronOS `focus_block`. External Google Calendar write-back is explicitly deferred.

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

## 7. Focus Block & Reflection Atomicity
When completing a focus block via `POST /api/v1/focus-blocks/{id}/complete`, the backend requires a reflection payload to update the block, insert the reflection, recalculate risk, advance the time spine, and update commitment progress all in a single transaction-like API flow to prevent state mismatches.

## 8. Time Spine Normalization
The `spine_json` array stored in the database only holds static label/id data. The backend `time_spine_service` dynamically normalizes this data based on the `current_stage` pointer to return actionable statuses (`active`, `pending`, `completed`) rather than duplicating stateful values inside the JSON array.
