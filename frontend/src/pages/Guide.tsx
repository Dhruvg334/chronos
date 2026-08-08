import { Link } from 'react-router-dom';

const pillars = [
  ['Capture', 'Put commitments into Inbox without turning capture into a form-filling exercise. ChronOS can separate outcomes, tasks, routines, events, dependencies, uncertain effort, and ambiguous deadlines while preserving your wording.'],
  ['Plan', 'Place meaningful work around actual availability, calendar events, transition buffers, protected intervals, focus limits, routines, project context, and dependency state.'],
  ['Focus and adapt', 'Work the next feasible action, record what really happened, and use recovery when interruptions, underestimation, blockers, or calendar changes invalidate the original plan.'],
];

export default function Guide() {
  return (
    <div className="min-h-screen bg-canvas">
      <header className="page-container flex h-16 items-center justify-between">
        <Link to="/" className="text-xl font-semibold">Chron<span className="text-accent">OS</span></Link>
        <Link to="/demo" className="text-sm font-medium text-muted">Guided demo</Link>
      </header>

      <main className="page-container py-12">
        <div className="mx-auto max-w-3xl">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent-strong">About ChronOS</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight">From scattered commitments to a realistic execution system</h1>
          <p className="mt-5 text-lg leading-8 text-muted">
            ChronOS combines what you need to do with the time, context, constraints, and working preferences you actually have. It recommends credible next actions, explains consequential suggestions, and keeps user approval at the boundary where plans or external systems could change.
          </p>

          <div className="mt-10 grid gap-4 sm:grid-cols-3">
            {pillars.map(([title, text], index) => (
              <section key={title} className="surface p-5">
                <span className="text-sm font-semibold text-accent-strong">0{index + 1}</span>
                <h2 className="mt-3 font-semibold">{title}</h2>
                <p className="mt-2 text-sm leading-6 text-muted">{text}</p>
              </section>
            ))}
          </div>

          <section className="mt-10 surface-subtle p-6">
            <h2 className="text-lg font-semibold">Your approval boundary</h2>
            <p className="mt-2 text-sm leading-6 text-muted">
              Reading internal context and preparing recommendations can happen automatically. Creating consequential internal changes remains policy-controlled, while sending messages, deleting data, changing permissions, or writing to external systems requires explicit approval.
            </p>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">What ChronOS understands</p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight">Planning is more than putting tasks on a calendar</h2>
            <div className="mt-5 space-y-4 text-sm leading-7 text-muted">
              <p>ChronOS works with projects, outcomes, commitments, routines, deadlines, effort estimates, dependencies, working hours, protected intervals, calendar events, transition buffers, and daily focus limits. The point is not to produce a visually neat schedule; it is to produce a schedule that can survive contact with the day.</p>
              <p>Daily and weekly planning remain capacity-aware. Work that is blocked, oversized, overlapping, outside availability, or incompatible with a protected interval is rejected by deterministic validation rather than being accepted because a language model suggested it.</p>
              <p>Projects represent meaningful bodies of work, outcomes represent completed states, and tasks remain executable actions. Routines support continuity without turning a missed day into a punitive streak mechanic.</p>
            </div>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">How the AI is used</p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight">Probabilistic where useful, deterministic where necessary</h2>
            <div className="mt-5 space-y-4 text-sm leading-7 text-muted">
              <p>Model-assisted workflows help interpret natural-language capture, diagnose planning conflicts, propose bounded candidate plans, explain trade-offs, identify ambiguity, and generate recovery options. These capabilities are useful because language and prioritization are inherently contextual.</p>
              <p>They do not get the final say on feasibility. Ownership, availability, overlap, protected-time, transition, capacity, deadline, dependency, permission, and approval rules are enforced outside the model.</p>
              <p>Every model-assisted workflow is bounded by request budgets, schema validation, error classification, limited repair, and graceful fallback. ChronOS can continue operating from structured data even when the model provider is unavailable.</p>
            </div>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">Memory and context</p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight">Context that remains inspectable</h2>
            <div className="mt-5 space-y-4 text-sm leading-7 text-muted">
              <p>ChronOS can retain explicit preferences, constraints, working patterns, project facts, decisions, and planning rules. Inferred memories are proposed rather than silently promoted to fact, and users can confirm, reject, edit, archive, or inspect their provenance.</p>
              <p>Notes and supported documents can be ingested into a hybrid retrieval layer that combines lexical and vector retrieval. Retrieved context remains attributable to its source, and document content is treated as untrusted data rather than as instructions that can override system behavior.</p>
              <p>Context packs assemble only the information relevant to a specific planning, recovery, project, focus, or reflection decision. Token budgets, source deduplication, provenance, uncertainty, and fallback behavior keep context bounded.</p>
            </div>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">Recovery</p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight">A plan is only useful if it can recover</h2>
            <div className="mt-5 space-y-4 text-sm leading-7 text-muted">
              <p>ChronOS treats overload, interruption, ambiguity, blocked dependencies, underestimated duration, start friction, low-energy periods, and calendar disruption as different failure modes. Recovery options are constrained by the remaining day instead of simply rescheduling everything later.</p>
              <p>The system presents a small number of feasible alternatives, their trade-offs, and one recommended path. A recovery suggestion can be dismissed, postponed, edited, or approved without hiding the fact that priorities changed.</p>
            </div>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">Security and control</p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight">User-owned data stays user-owned</h2>
            <div className="mt-5 space-y-4 text-sm leading-7 text-muted">
              <p>ChronOS uses Supabase Auth, row-level security, composite ownership constraints, transactional RPCs, restricted security-definer functions, and Vault-backed token references. Cross-user reads, writes, approvals, retrieval, and integration access are explicitly denied.</p>
              <p>External integrations are read-first. Normalized external data is treated as attributed context, not as authority. Inbox proposals generated from external sources still require review before they become ChronOS work or memory.</p>
              <p>Operational controls include rate limits, request budgets, bounded retries, idempotency, rollback, data export, account deletion, retention policies, and concise audit events without raw secrets, documents, prompts, or hidden reasoning.</p>
            </div>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">System architecture</p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight">A full-stack planning system, not a chatbot wrapper</h2>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <div className="surface p-5"><h3 className="font-semibold">Frontend</h3><p className="mt-2 text-sm leading-6 text-muted">React, Vite, TypeScript, protected routes, TanStack Query, responsive product flows, progressive disclosure, and approval-focused interactions.</p></div>
              <div className="surface p-5"><h3 className="font-semibold">Backend</h3><p className="mt-2 text-sm leading-6 text-muted">FastAPI, Pydantic, repository boundaries, bounded workflows, quotas, failure taxonomy, operational health, and provider-neutral AI/integration abstractions.</p></div>
              <div className="surface p-5"><h3 className="font-semibold">Data</h3><p className="mt-2 text-sm leading-6 text-muted">Supabase Postgres, Auth, RLS, Vault, pgvector, transactional writes, migrations, memory, knowledge, audit, and lifecycle controls.</p></div>
              <div className="surface p-5"><h3 className="font-semibold">AI and integrations</h3><p className="mt-2 text-sm leading-6 text-muted">Groq-backed structured workflows, provider-neutral embeddings, Google Calendar context, read-first external connectors, and restricted MCP foundations.</p></div>
            </div>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">Evaluation</p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight">Designed to be tested, not merely demonstrated</h2>
            <div className="mt-5 space-y-4 text-sm leading-7 text-muted">
              <p>ChronOS combines offline unit coverage, live Supabase ownership and transaction tests, provider-live Groq verification, frontend interaction tests, migration validation, security checks, and versioned synthetic evaluation datasets.</p>
              <p>Evaluation results are interpreted narrowly. Synthetic fixtures prove regression behavior and validator consistency; they are not presented as evidence of broad production intelligence. That distinction is intentional.</p>
            </div>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">The product philosophy</p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight">Quietly useful beats aggressively autonomous</h2>
            <p className="mt-5 text-sm leading-7 text-muted">
              ChronOS is designed to reduce planning friction without taking ownership away from the person doing the work. The system should speak up when constraints matter, stay quiet when deterministic logic is enough, explain consequential recommendations, and remain useful when integrations or model providers are degraded.
            </p>
          </section>

          <div className="mt-12 flex flex-col items-start justify-between gap-4 border-t border-line pt-8 sm:flex-row sm:items-center">
            <div><h2 className="text-lg font-semibold">See the system in action</h2><p className="mt-1 text-sm text-muted">Walk through a static planning scenario without creating an account.</p></div>
            <Link to="/demo" className="button-primary">Open guided demo</Link>
          </div>
        </div>
      </main>
    </div>
  );
}
