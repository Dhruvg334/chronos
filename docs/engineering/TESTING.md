# Testing

Default tests are offline. They must not open sockets, local ports, Docker, Supabase, Google, or Groq. Clear external configuration before application imports and override dependencies with fakes.

Backend:

```powershell
cd backend
python -m pytest
python -m pytest -m integration
```

The integration suite is opt-in and reports missing configuration as a skip.

Frontend:

```powershell
cd frontend
npm ci
npm run typecheck
npm run lint
npm run test -- --run
npm run build
```

Frontend tests use Vitest, React Testing Library, jsdom, and mocked browser/network boundaries. They do not require the backend.

Manual profiles: open `/demo` logged out; open `/today` logged out; test invalid email `dhruv`, weak password `password`, mismatched `Chronos123!`/`Chronos456!`; use the documented multi-commitment Inbox sample; verify logout clears the session and protected views.
