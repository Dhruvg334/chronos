# Deployment

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

Set `BACKEND_CORS_ORIGINS` to a JSON array containing local development origins and the exact final Netlify origin, for example `["http://localhost:5173","https://chronos-example.netlify.app"]`. Deploy previews are disabled unless `BACKEND_CORS_ORIGIN_REGEX` is explicitly set to an anchored, site-specific expression such as `^https://deploy-preview-[0-9]+--chronos-example\.netlify\.app$`. Do not use a wildcard Netlify origin regex with credentialed CORS.
