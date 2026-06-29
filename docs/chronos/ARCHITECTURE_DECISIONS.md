# ChronOS Architecture Decisions

1. **Supabase Stack**: Auth, Postgres, RLS, Vault, pgvector (for future embeddings).
2. **Backend**: FastAPI, Python 3.12, async routing, direct Supabase python client.
3. **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons, React Router.
4. **Agent Orchestration**: LangGraph for stateful decision making (`langgraph==0.0.60`).
5. **Security**: Supabase Vault used to store Google OAuth tokens. No plaintext tokens in database. Service role required for decryption.
6. **UI Language**: Uses semantic tokens defined in `tailwind.config.js`. Warm ivory (`bg-warm-cream`), clean white cards, subtle borders (`border-warm-border`), soft amber primary actions (`bg-accent-amber`). Command dashboard strictly matches Settings layout (progressive disclosure, generous spacing, max-w-3xl, zero operational clutter). In-product guidance using lightweight hover hints.
