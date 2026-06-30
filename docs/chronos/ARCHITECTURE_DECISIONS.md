# ChronOS Architecture Decisions

1. **Supabase Stack**: Auth, Postgres, RLS, Vault, pgvector (for future embeddings).
2. **Backend**: FastAPI, Python 3.12, async routing, direct Supabase python client.
3. **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons, React Router.
4. **Agent Orchestration**: LangGraph for stateful decision making (`langgraph==0.0.60`).
5. **Security**: Supabase Vault used to store Google OAuth tokens. No plaintext tokens in database. Service role required for decryption.
6. **UI Language & Layout Rules**: Uses semantic tokens defined in `tailwind.config.js`. Warm ivory (`bg-warm-ivory`), clean white containers, subtle borders (`border-warm-border`), soft amber primary actions (`bg-accent-amber`). No hardcoded hex values. 
7. **Layout Widths**: Wide workspace pages (Command, Inbox, Calendar, Rescue, Reflection) utilize `max-w-6xl` for broad horizontal real estate to prevent title truncation. Narrow utility pages (Settings, About, Login, Signup) use `max-w-3xl` or `max-w-4xl` for calm, focused reading and form entry.
