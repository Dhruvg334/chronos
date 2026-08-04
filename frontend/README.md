# ChronOS frontend

The frontend is a React and TypeScript single-page application built with Vite. It owns authentication-aware navigation, product presentation, accessibility, and client-side server-state coordination through TanStack Query.

## Environment

Copy `.env.example` to `.env` and configure only the public browser values:

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_SUPABASE_URL=http://127.0.0.1:55321
VITE_SUPABASE_ANON_KEY=...
```

Never place service-role, model-provider, OAuth client-secret, encryption, or integration credentials in the frontend environment.

## Commands

```powershell
npm run dev
npm run typecheck
npm run lint
npm run test -- --run
npm run build
```

Install dependencies on first setup or after `package.json` or `package-lock.json` changes.

## Application surfaces

- Public: landing, guide, static demo, login, and signup
- Primary authenticated navigation: Today, Inbox, and Plan
- Contextual planning: Week, Projects, Outcomes, Routines, Focus, Recovery, and Reflection
- Utility: onboarding, preferences, memory and knowledge, integrations, data controls, and operational traces

Private query data is cleared on logout. Protected API calls use the active Supabase access token through the shared `apiFetch` helper.
