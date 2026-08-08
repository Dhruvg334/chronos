import { ArrowRight, CheckCircle2, Clock3, Database, FileText, Focus, ShieldCheck, Workflow } from 'lucide-react';
import { Link } from 'react-router-dom';
import { StrategyRecommendationCard } from '../components/strategy/StrategyRecommendationCard';

const plan = [
  { time: '09:00', title: 'Authentication regression fix', detail: '60 minutes · urgent and important' },
  { time: '10:15', title: 'Review deployment notes', detail: '25 minutes · batched review' },
  { time: '11:00', title: 'Prepare Monday slides', detail: '45-minute first focus interval' },
];

const captured = [
  ['Authentication fix', 'Task', 'Due tomorrow afternoon · estimate 60 min'],
  ['Monday presentation', 'Outcome', 'Effort uncertain · screenshots dependency detected'],
  ['Team sync', 'Event', 'Fixed at 4:00 PM'],
  ['Database assignment', 'Task', 'Due Tuesday morning'],
];

const recoveryOptions = [
  ['Finish a 20-minute minimum slice', 'Protect progress before the next fixed event.'],
  ['Move the remaining work', 'Create a feasible block tomorrow instead of overrunning today.'],
  ['Stop and reflect', 'Record the interruption and preserve the rest of the plan.'],
];

const steps = ['Capture', 'Validate', 'Explain', 'Focus', 'Recover', 'Context', 'Integrate', 'Degrade safely'];

export default function Demo() {
  return (
    <div className="min-h-screen bg-[#FAFAF8] text-ink">
      <header className="border-b border-line bg-white/90 backdrop-blur">
        <div className="page-container flex h-[68px] items-center justify-between">
          <Link to="/" className="text-xl font-semibold tracking-[-0.035em]">Chron<span className="text-accent">OS</span></Link>
          <div className="flex items-center gap-2"><Link to="/guide" className="button-ghost">About</Link><Link to="/signup" className="button-primary-accent">Get started</Link></div>
        </div>
      </header>

      <main>
        <section className="border-b border-line bg-white">
          <div className="page-container grid gap-10 py-14 lg:grid-cols-[1fr_0.9fr] lg:items-end lg:py-18">
            <div className="max-w-3xl"><p className="eyebrow">Guided demo · static and private</p><h1 className="mt-4 text-balance text-[clamp(2.8rem,5.5vw,5rem)] font-semibold leading-[0.98] tracking-[-0.055em]">A busy day, made credible</h1><p className="mt-5 max-w-2xl text-[17px] leading-8 text-muted">This public scenario uses static data. It does not authenticate, poll protected APIs, or access a workspace. The goal is to show the product logic without pretending to be your real day.</p></div>
            <div className="grid grid-cols-2 gap-3 rounded-[22px] border border-[#E5DDD4] bg-[#FCF7F1] p-5 sm:grid-cols-4 lg:grid-cols-2">
              <div><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">Available</p><p className="mt-1 text-lg font-semibold">240 min</p></div>
              <div><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">Fixed events</p><p className="mt-1 text-lg font-semibold">2</p></div>
              <div><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">Blocked work</p><p className="mt-1 text-lg font-semibold">1</p></div>
              <div><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">Decision</p><p className="mt-1 text-lg font-semibold text-accent-strong">1 pending</p></div>
            </div>
          </div>
        </section>

        <div className="page-container py-12">
          <div className="grid gap-10 lg:grid-cols-[170px_minmax(0,1fr)] lg:gap-12">
            <aside className="hidden lg:block"><div className="sticky top-8"><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">Walkthrough</p><ol className="mt-4 space-y-1">{steps.map((step, index) => <li key={step}><a href={`#demo-${index + 1}`} className="flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm text-muted transition hover:bg-white hover:text-ink"><span className="w-5 text-[10px] font-semibold text-accent-strong">0{index + 1}</span>{step}</a></li>)}</ol></div></aside>

            <div className="min-w-0">
              <div className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
                <section className="rounded-[22px] border border-line bg-white p-6 shadow-[0_12px_36px_rgba(42,35,28,0.04)]">
                  <div className="flex items-start justify-between gap-4"><div><p className="text-sm font-medium text-success">Plan is workable after one deferral</p><h2 className="mt-2 text-2xl font-semibold tracking-[-0.025em]">Finish the authentication fix</h2></div><CheckCircle2 className="mt-1 h-6 w-6 shrink-0 text-success" /></div>
                  <ol className="mt-7 divide-y divide-line border-y border-line">{plan.map(item => <li key={item.time} className="grid grid-cols-[58px_1fr] gap-4 py-4"><span className="text-sm font-semibold text-accent-strong">{item.time}</span><div><h3 className="font-medium">{item.title}</h3><p className="mt-1 text-sm text-muted">{item.detail}</p></div></li>)}</ol>
                  <div className="mt-5 flex items-start gap-2 rounded-xl bg-[#FCF7F1] p-4 text-sm leading-6 text-muted"><Clock3 className="mt-0.5 h-4 w-4 shrink-0 text-accent" />The database assignment moves to a protected block tomorrow morning. Nothing changes automatically.</div>
                </section>

                <aside className="space-y-4"><section className="rounded-[22px] border border-[#E5DDD4] bg-[#FCF7F1] p-5"><div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-accent" /><h2 className="font-semibold">One decision waiting</h2></div><p className="mt-3 text-sm leading-6 text-muted">Approve the explicit deferral, or choose a smaller slide scope. External calendars remain unchanged.</p></section><StrategyRecommendationCard recommendation={{ strategy: 'constrained_day', title: 'Constrain the day', why: 'The original work exceeds the 240 minutes available.', evidence: ['one 150-minute outcome', 'five short tasks', '240 free minutes'], action: 'Protect one major outcome and defer lower-value work explicitly.', tradeoff: 'Some work moves to tomorrow.', automatic_change: false, confidence: 'high', alternatives: [] }} /></aside>
              </div>

              <section id="demo-1" className="mt-14 scroll-mt-8 border-t border-line pt-9">
                <div className="grid gap-7 lg:grid-cols-[0.72fr_1.28fr]"><div><p className="eyebrow">01 · Capture</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">Start with messy reality, not a perfect form</h2><p className="mt-4 text-sm leading-7 text-muted">A single natural-language capture can contain tasks, outcomes, events, uncertainty, and dependencies. ChronOS separates them without inventing certainty.</p></div><div className="grid gap-3 sm:grid-cols-2">{captured.map(([title, kind, detail]) => <article key={title} className="rounded-2xl border border-line bg-white p-4"><div className="flex items-center justify-between gap-3"><h3 className="font-medium">{title}</h3><span className="text-xs font-semibold text-accent-strong">{kind}</span></div><p className="mt-2 text-sm leading-6 text-muted">{detail}</p></article>)}</div></div>
              </section>

              <section id="demo-2" className="mt-14 scroll-mt-8 border-t border-line pt-9">
                <p className="eyebrow">02 · Validate capacity</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">A plan has to fit before it can be useful</h2>
                <div className="mt-6 grid gap-4 sm:grid-cols-3"><article className="rounded-2xl border border-line bg-white p-5"><Clock3 className="h-5 w-5 text-accent" /><h3 className="mt-3 font-semibold">Availability</h3><p className="mt-2 text-sm leading-6 text-muted">09:30–18:30 working window, protected lunch, transition buffers, and a daily focus limit.</p></article><article className="rounded-2xl border border-line bg-white p-5"><Database className="h-5 w-5 text-accent" /><h3 className="mt-3 font-semibold">Calendar reality</h3><p className="mt-2 text-sm leading-6 text-muted">Fixed events reduce capacity. Cached or degraded states remain visible rather than silently ignored.</p></article><article className="rounded-2xl border border-line bg-white p-5"><Workflow className="h-5 w-5 text-accent" /><h3 className="mt-3 font-semibold">Dependencies</h3><p className="mt-2 text-sm leading-6 text-muted">Blocked work is not scheduled as executable focus merely because it has a deadline.</p></article></div>
              </section>

              <section id="demo-3" className="mt-14 scroll-mt-8 border-t border-line pt-9"><p className="eyebrow">03 · Explain the plan</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">The recommendation is inspectable</h2><div className="mt-6 grid gap-4 md:grid-cols-2"><article className="rounded-2xl border border-line bg-white p-5"><h3 className="font-semibold">Why this next action?</h3><ul className="mt-4 space-y-2 text-sm leading-6 text-muted"><li>Near deadline and credible 60-minute estimate.</li><li>Fits before the fixed team event.</li><li>Slide work is uncertain and dependency-blocked.</li><li>Deferral preserves today’s focus limit.</li></ul></article><article className="rounded-2xl border border-line bg-white p-5"><h3 className="font-semibold">What the system does not do</h3><ul className="mt-4 space-y-2 text-sm leading-6 text-muted"><li>Silently move calendar events.</li><li>Turn inferred context into fact.</li><li>Persist an AI-generated plan before validation and approval.</li></ul></article></div></section>

              <section id="demo-4" className="mt-14 scroll-mt-8 border-t border-line pt-9"><p className="eyebrow">04 · Focus</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">Execution stays connected to the plan</h2><div className="mt-6 rounded-[22px] border border-[#E5DDD4] bg-[#FCF7F1] p-6"><div className="flex items-start gap-4"><Focus className="mt-0.5 h-5 w-5 shrink-0 text-accent" /><div><h3 className="font-semibold">Authentication regression fix · 60 minutes</h3><p className="mt-2 text-sm leading-6 text-muted">Start, pause, resume, complete, or stop. Completion can record actual time, partial progress, energy, and a concise reflection so future plans are grounded in what really happened.</p></div></div></div></section>

              <section id="demo-5" className="mt-14 scroll-mt-8 border-t border-line pt-9"><p className="eyebrow">05 · Recover</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">When the day changes, recovery is constrained too</h2><p className="mt-4 max-w-3xl text-sm leading-7 text-muted">If a focus block is interrupted after 20 minutes and another meeting begins in 30 minutes, continuing the remaining 40 minutes is no longer feasible. ChronOS diagnoses the disruption instead of pretending the original plan still works.</p><div className="mt-6 grid gap-3 sm:grid-cols-3">{recoveryOptions.map(([title, text]) => <article key={title} className="rounded-2xl border border-line bg-white p-5"><h3 className="font-semibold">{title}</h3><p className="mt-2 text-sm leading-6 text-muted">{text}</p></article>)}</div></section>

              <section id="demo-6" className="mt-14 scroll-mt-8 border-t border-line pt-9"><p className="eyebrow">06 · Context and provenance</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">Recommendations can cite what influenced them</h2><div className="mt-6 grid gap-4 sm:grid-cols-2"><article className="rounded-2xl border border-line bg-white p-5"><FileText className="h-5 w-5 text-accent" /><h3 className="mt-3 font-semibold">Project context</h3><p className="mt-2 text-sm leading-6 text-muted">“Production readiness requires stable authentication, verified rollback, deployment documentation, and responsive onboarding.” The source remains inspectable when it materially affects planning.</p></article><article className="rounded-2xl border border-line bg-white p-5"><ShieldCheck className="h-5 w-5 text-accent" /><h3 className="mt-3 font-semibold">Confirmed preference</h3><p className="mt-2 text-sm leading-6 text-muted">“I prefer 45-minute focus blocks and do not want important work immediately after meetings.” Explicit preferences outrank inferred patterns.</p></article></div></section>

              <section id="demo-7" className="mt-14 scroll-mt-8 border-t border-line pt-9"><p className="eyebrow">07 · External context</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">Integrations provide context before they provide control</h2><p className="mt-4 text-sm leading-7 text-muted">Calendar, email, project, note, and task integrations normalize external information into attributed context and Inbox proposals. External content remains untrusted. Read access and proposal generation are separate from write authority.</p></section>

              <section id="demo-8" className="mt-14 scroll-mt-8 border-t border-line pt-9"><p className="eyebrow">08 · Reliability</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">The system is designed to degrade instead of collapse</h2><div className="mt-5 grid gap-4 text-sm leading-7 text-muted md:grid-cols-2"><p>If Groq is unavailable, deterministic planning state still loads. If retrieval fails, planning can continue from structured project and calendar data. If calendar data is stale, its source and confidence remain visible.</p><p>Atomic database functions protect multi-write actions from partial completion, while RLS and ownership constraints keep one user’s plans, memory, context, integrations, and approvals isolated from another user.</p></div></section>

              <div className="mt-14 flex flex-col justify-between gap-5 rounded-[22px] border border-[#E5DDD4] bg-[#FCF7F1] p-6 sm:flex-row sm:items-center"><div><p className="eyebrow">Your turn</p><h2 className="mt-2 text-xl font-semibold">Use the same loop with your own commitments</h2><p className="mt-1 text-sm text-muted">Capture, review, plan, focus, and recover with clear approval boundaries.</p></div><Link className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-accent px-4 text-sm font-semibold text-white" to="/signup">Create an account <ArrowRight className="h-4 w-4" /></Link></div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
