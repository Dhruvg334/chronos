# Deployment

Runtime Python dependencies are in `backend/requirements.txt`; test tooling is in `backend/requirements-dev.txt`. Public liveness is `/api/v1/health/live`, public bounded readiness is `/api/v1/health/ready`, and authenticated detail is `/api/v1/operations/status`.

Configure rate limits, CORS origins, trusted hosts, provider credentials, and retention operations with backend-only environment settings. Netlify receives only `VITE_API_URL`, `VITE_SUPABASE_URL`, and `VITE_SUPABASE_ANON_KEY`. CSP and related headers are in `netlify.toml`; backend secrets never belong in frontend variables.

The current client-only SPA does not enable React Router RSC or server-action modes. The package advisory database nevertheless reports the RSC CSRF advisory against `react-router-dom` 7.18.2, and no fixed compatible release is published in the configured registry. Do not enable those modes; upgrade and revalidate as soon as a fixed release is available.

The frontend and API deploy independently. Netlify serves only the compiled Vite application; FastAPI runs on a Python web service with Supabase as its persistent store. Neither service relies on a local persistent filesystem.

## Netlify frontend

Import the repository and use the committed `netlify.toml`. It builds from `frontend` with Node 22.12, publishes `frontend/dist`, and rewrites unmatched routes to `index.html` for the SPA router.

Configure these public build-time variables in Netlify:

- `VITE_API_URL`: the HTTPS origin of the separately deployed FastAPI service, without a trailing slash.
- `VITE_SUPABASE_URL`: the project Supabase URL.
- `VITE_SUPABASE_ANON_KEY`: the public Supabase anon key.

Never add the Supabase service-role key, Groq key, Google client secret, OAuth state secret, or encryption key to Netlify.

## FastAPI service

Use Python 3.12.10 with `backend` as the service root.

- Install: `python -m pip install --no-cache-dir -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Liveness: `GET /api/v1/health/live`

Render configuration: create a Python web service, set root directory `backend`, use the install and start commands above, and set `/api/v1/health/live` as the health-check path. Koyeb uses the same root, build command, run command, environment, and health path.

Required backend environment includes `ENV=production`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `FRONTEND_URL`, and `BACKEND_CORS_ORIGINS`. Configure Groq variables when model-assisted features are enabled and Google/Vault variables when read-only Calendar is enabled; use `backend/.env.example` as the complete inventory. The hosting platform supplies `PORT`.

Context defaults to the offline `local_hash` embedding fallback. For semantic retrieval, configure `EMBEDDING_PROVIDER=huggingface`, `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`, backend-only `EMBEDDING_API_KEY`, `EMBEDDING_BASE_URL`, dimensions, timeout, retries, file-size limit, and context token budget. Never expose embedding credentials or service-role access to the frontend. The API does not rely on local persistent files; uploads are extracted in memory and persisted atomically to Supabase.

Set `BACKEND_CORS_ORIGINS` to a JSON array containing local development origins and the exact final Netlify origin, for example `["http://localhost:5173","https://chronos-example.netlify.app"]`. Deploy previews are disabled unless `BACKEND_CORS_ORIGIN_REGEX` is explicitly set to an anchored, site-specific expression such as `^https://deploy-preview-[0-9]+--chronos-example\.netlify\.app$`. Do not use a wildcard Netlify origin regex with credentialed CORS.

Optional integration variables are documented in `backend/.env.example`. Google, Gmail, GitHub, Notion, and Microsoft secrets are backend-only. `MCP_ALLOWED_SERVERS` contains exact hostnames; arbitrary URLs are rejected and remote execution remains disabled until a validated transport is configured. The frontend receives safe status, scope names, selected-resource labels, timestamps, summaries, and citations only.
