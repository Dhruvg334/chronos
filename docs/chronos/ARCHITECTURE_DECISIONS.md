# ChronOS Architecture Decisions

1. **Supabase Stack**: Auth, Postgres, RLS, Vault, pgvector (for future embeddings).
2. **Backend**: FastAPI, Python 3.12, async routing, direct Supabase python client.
3. **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons, React Router.
4. **Agent Orchestration**: LangGraph for stateful decision making (`langgraph==0.0.60`).
5. **Security**: Supabase Vault used to store Google OAuth tokens. No plaintext tokens in database. Service role required for decryption.
6. **UI Language**: Warm ivory (`#FAF9F6`), clean white cards, soft amber/orange accents (`#B57C45`). Calm urgency. No heavy, intimidating hacker dashboards. In-product guidance using lightweight hover hints.
