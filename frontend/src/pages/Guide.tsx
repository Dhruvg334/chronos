import { ArrowRight, CheckCircle2, ShieldCheck, Sparkles, TimerReset } from 'lucide-react';
import { Link } from 'react-router-dom';

const pillars = [
  ['Capture', 'Put commitments into Inbox without turning capture into a form-filling exercise. ChronOS separates outcomes, tasks, routines, events, dependencies, uncertain effort, and ambiguous deadlines while preserving your wording.'],
  ['Plan', 'Place meaningful work around actual availability, calendar events, transition buffers, protected intervals, focus limits, routines, project context, and dependency state.'],
  ['Focus and adapt', 'Work the next feasible action, record what really happened, and recover when interruptions, underestimation, blockers, or calendar changes invalidate the original plan.'],
];

const architecture = [
  ['Frontend', 'React, Vite, TypeScript, protected routes, TanStack Query, responsive product flows, progressive disclosure, and approval-focused interactions.'],
  ['Backend', 'FastAPI, Pydantic, repository boundaries, bounded workflows, quotas, failure taxonomy, health checks, and provider-neutral AI/integration abstractions.'],
  ['Data', 'Supabase Postgres, Auth, RLS, Vault, pgvector, transactional writes, migrations, memory, knowledge, audit, and lifecycle controls.'],
  ['AI + integrations', 'Groq-backed structured workflows, provider-neutral embeddings, Google Calendar context, read-first external connectors, and restricted MCP foundations.'],
];

const toc = [
  ['product', 'Product model'],
  ['ai', 'AI boundaries'],
  ['context', 'Memory + context'],
  ['recovery', 'Recovery'],
  ['security', 'Security'],
  ['architecture', 'Architecture'],
];

export default function Guide() {
  return (
    <div className="min-h-screen bg-[#FAFAF8] text-ink">
      <header className="border-b border-line bg-white/90 backdrop-blur">
        <div className="page-container flex h-[68px] items-center justify-between">
          <Link to="/" className="text-xl font-semibold tracking-[-0.035em]">Chron<span className="text-accent">OS</span></Link>
          <div className="flex items-center gap-2"><Link to="/demo" className="button-ghost">Guided demo</Link><Link to="/signup" className="button-primary-accent">Get started</Link></div>
        </div>
      </header>

      <main>
        <section className="border-b border-line bg-white">
          <div className="page-container grid gap-10 py-16 lg:grid-cols-[1.15fr_0.85fr] lg:items-end lg:py-20">
            <div className="max-w-3xl">
              <p className="eyebrow">About ChronOS</p>
              <h1 className="mt-4 text-balance text-[clamp(2.8rem,5.6vw,5.2rem)] font-semibold leading-[0.98] tracking-[-0.055em]">From scattered commitments to a realistic execution system</h1>
              <p className="mt-6 max-w-[760px] text-[17px] leading-8 text-muted">ChronOS combines what you need to do with the time, context, constraints, and working preferences you actually have. It recommends credible next actions, explains consequential suggestions, and keeps approval at the boundary where plans or external systems could change.</p>
            </div>

            <aside className="rounded-[22px] border border-[#E5DDD4] bg-[#FCF7F1] p-6">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-accent-strong">Core idea</p>
              <p className="mt-3 text-xl font-semibold leading-7 tracking-[-0.025em]">AI may interpret the situation. Deterministic systems decide what is feasible.</p>
              <div className="mt-5 flex items-center gap-2 text-sm text-muted"><ShieldCheck className="h-4 w-4 text-accent" /> Approval-first by design</div>
            </aside>
          </div>
        </section>

        <section className="page-container py-14 lg:py-18">
          <div className="grid gap-10 lg:grid-cols-[200px_minmax(0,1fr)] lg:gap-14">
            <aside className="hidden lg:block">
              <div className="sticky top-8">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">On this page</p>
                <nav className="mt-4 space-y-1" aria-label="About sections">
                  {toc.map(([id, label]) => <a key={id} href={`#${id}`} className="block rounded-lg px-3 py-2 text-sm font-medium text-muted transition hover:bg-white hover:text-ink">{label}</a>)}
                </nav>
              </div>
            </aside>

            <div className="min-w-0">
              <section className="grid gap-4 sm:grid-cols-3">
                {pillars.map(([title, text], index) => <article key={title} className="rounded-2xl border border-line bg-white p-5 shadow-[0_8px_24px_rgba(42,35,28,0.03)]"><span className="text-xs font-semibold text-accent-strong">0{index + 1}</span><h2 className="mt-3 text-lg font-semibold tracking-[-0.02em]">{title}</h2><p className="mt-2 text-sm leading-6 text-muted">{text}</p></article>)}
              </section>

              <section className="mt-8 rounded-[22px] border border-[#E5DDD4] bg-[#FCF7F1] p-6 sm:p-7">
                <div className="flex items-start gap-4"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white text-accent shadow-sm"><CheckCircle2 className="h-5 w-5" /></span><div><h2 className="text-lg font-semibold">Your approval boundary</h2><p className="mt-2 text-sm leading-7 text-muted">Reading internal context and preparing recommendations can happen automatically. Consequential internal changes remain policy-controlled, while sending messages, deleting data, changing permissions, or writing to external systems requires explicit approval.</p></div></div>
              </section>

              <section id="product" className="mt-14 scroll-mt-8 border-t border-line pt-9">
                <p className="eyebrow">Product model</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">Planning is more than putting tasks on a calendar</h2>
                <div className="mt-5 grid gap-5 text-sm leading-7 text-muted md:grid-cols-2"><p>ChronOS works with projects, outcomes, commitments, routines, deadlines, effort estimates, dependencies, working hours, protected intervals, calendar events, transition buffers, and daily focus limits. The goal is not a visually neat schedule; it is a schedule that can survive contact with the day.</p><p>Daily and weekly planning remain capacity-aware. Work that is blocked, oversized, overlapping, outside availability, or incompatible with protected time is rejected by deterministic validation rather than accepted because a model suggested it.</p></div>
              </section>

              <section id="ai" className="mt-14 scroll-mt-8 border-t border-line pt-9">
                <p className="eyebrow">How AI is used</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">Probabilistic where useful. Deterministic where necessary.</h2>
                <div className="mt-6 grid gap-4 md:grid-cols-3">
                  <article className="rounded-2xl border border-line bg-white p-5"><Sparkles className="h-5 w-5 text-accent" /><h3 className="mt-3 font-semibold">Interpret</h3><p className="mt-2 text-sm leading-6 text-muted">Natural-language capture, ambiguity, planning conflicts, and recovery options.</p></article>
                  <article className="rounded-2xl border border-line bg-white p-5"><ShieldCheck className="h-5 w-5 text-accent" /><h3 className="mt-3 font-semibold">Validate</h3><p className="mt-2 text-sm leading-6 text-muted">Ownership, overlap, capacity, dependencies, deadlines, permissions, and approval rules.</p></article>
                  <article className="rounded-2xl border border-line bg-white p-5"><TimerReset className="h-5 w-5 text-accent" /><h3 className="mt-3 font-semibold">Degrade safely</h3><p className="mt-2 text-sm leading-6 text-muted">Structured planning continues when providers, retrieval, or calendar context become unavailable.</p></article>
                </div>
              </section>

              <section id="context" className="mt-14 scroll-mt-8 border-t border-line pt-9">
                <p className="eyebrow">Memory and context</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">Context stays attributable and editable</h2>
                <div className="mt-5 space-y-4 text-sm leading-7 text-muted"><p>ChronOS can retain explicit preferences, constraints, working patterns, project facts, decisions, and planning rules. Inferred memories are proposed rather than silently promoted to fact, and users can confirm, reject, edit, archive, or inspect their provenance.</p><p>Notes and supported documents feed a hybrid retrieval layer that combines lexical and vector retrieval. Retrieved context remains tied to its source, while document content is treated as untrusted data rather than instructions.</p><p>Context packs assemble only what is relevant to a specific planning, recovery, project, focus, or reflection decision, with token budgets, source deduplication, provenance, uncertainty, and fallback behavior.</p></div>
              </section>

              <section id="recovery" className="mt-14 scroll-mt-8 border-t border-line pt-9">
                <p className="eyebrow">Recovery</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">A plan is only useful if it can recover</h2>
                <p className="mt-5 text-sm leading-7 text-muted">ChronOS treats overload, interruption, ambiguity, blocked dependencies, underestimated duration, start friction, low-energy periods, and calendar disruption as different failure modes. It presents a small number of feasible alternatives, their trade-offs, and one recommended path without hiding the fact that priorities changed.</p>
              </section>

              <section id="security" className="mt-14 scroll-mt-8 border-t border-line pt-9">
                <p className="eyebrow">Security and control</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">User-owned data stays user-owned</h2>
                <div className="mt-5 grid gap-5 text-sm leading-7 text-muted md:grid-cols-2"><p>Supabase Auth, row-level security, composite ownership constraints, transactional RPCs, restricted security-definer functions, and Vault-backed token references isolate data and approvals by user.</p><p>External integrations are read-first. Operational controls add rate limits, request budgets, bounded retries, idempotency, rollback, export, deletion, retention policies, and concise audit events without raw secrets, prompts, documents, or hidden reasoning.</p></div>
              </section>

              <section id="architecture" className="mt-14 scroll-mt-8 border-t border-line pt-9">
                <p className="eyebrow">System architecture</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">A full-stack planning system, not a chatbot wrapper</h2>
                <div className="mt-6 grid gap-3 sm:grid-cols-2">{architecture.map(([title, text]) => <article key={title} className="rounded-2xl border border-line bg-white p-5"><h3 className="font-semibold">{title}</h3><p className="mt-2 text-sm leading-6 text-muted">{text}</p></article>)}</div>
              </section>

              <div className="mt-14 flex flex-col justify-between gap-5 rounded-[22px] border border-[#E5DDD4] bg-[#FCF7F1] p-6 sm:flex-row sm:items-center"><div><p className="eyebrow">See the system in motion</p><h2 className="mt-2 text-xl font-semibold">Walk through a complete planning day</h2></div><Link to="/demo" className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-accent px-4 text-sm font-semibold text-white">Open guided demo <ArrowRight className="h-4 w-4" /></Link></div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
