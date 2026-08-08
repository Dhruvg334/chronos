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

export default function Demo() {
  return (
    <div className="min-h-screen bg-canvas">
      <header className="page-container flex h-16 items-center justify-between">
        <Link to="/" className="text-xl font-semibold">Chron<span className="text-accent">OS</span></Link>
        <div className="flex items-center gap-3"><Link to="/about" className="text-sm font-medium text-muted">About</Link><Link to="/signup" className="button-primary">Sign up</Link></div>
      </header>

      <main className="page-container py-10">
        <div className="mx-auto max-w-5xl">
          <div className="mb-8 max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent-strong">Guided demo · static and private</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight">A busy day, made credible</h1>
            <p className="mt-4 text-lg leading-8 text-muted">This public scenario uses static data. It does not authenticate, poll protected APIs, or access a workspace.</p>
          </div>

          <div className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
            <section className="surface p-6">
              <div className="flex items-center justify-between"><div><p className="text-sm font-medium text-success">Plan is workable after one deferral</p><h2 className="mt-2 text-2xl font-semibold">Finish the authentication fix</h2></div><CheckCircle2 className="h-6 w-6 text-success" /></div>
              <ol className="mt-7 space-y-2">{plan.map(item => <li key={item.time} className="flex gap-4 rounded-xl bg-surface-subtle p-4"><span className="text-sm font-semibold text-accent-strong">{item.time}</span><div><h3 className="font-medium">{item.title}</h3><p className="mt-1 text-sm text-muted">{item.detail}</p></div></li>)}</ol>
              <div className="mt-5 flex items-start gap-2 rounded-xl border border-line p-4 text-sm text-muted"><Clock3 className="mt-0.5 h-4 w-4 shrink-0" />The database assignment moves to a protected block tomorrow morning. Nothing changes automatically.</div>
            </section>
            <aside className="space-y-5"><section className="surface p-5"><div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-accent" /><h2 className="font-semibold">One decision waiting</h2></div><p className="mt-3 text-sm leading-6 text-muted">Approve the explicit deferral, or choose a smaller slide scope. External calendars remain unchanged.</p></section><StrategyRecommendationCard recommendation={{ strategy: 'constrained_day', title: 'Constrain the day', why: 'The original work exceeds the 240 minutes available.', evidence: ['one 150-minute outcome', 'five short tasks', '240 free minutes'], action: 'Protect one major outcome and defer lower-value work explicitly.', tradeoff: 'Some work moves to tomorrow.', automatic_change: false, confidence: 'high', alternatives: [] }} /></aside>
          </div>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">01 · Capture</p>
            <h2 className="mt-3 text-2xl font-semibold">Start with messy reality, not a perfect form</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-muted">Imagine entering: “I need to finish the authentication regression fix before tomorrow afternoon, prepare slides for Monday, attend a team call at 4 PM, and submit my database assignment by Tuesday morning. The auth fix needs around an hour. I do not know how long the slides will take, and I am waiting for screenshots.” ChronOS separates the work without inventing certainty.</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">{captured.map(([title, kind, detail]) => <div key={title} className="surface p-4"><div className="flex items-center justify-between gap-3"><h3 className="font-medium">{title}</h3><span className="text-xs font-semibold text-accent-strong">{kind}</span></div><p className="mt-2 text-sm leading-6 text-muted">{detail}</p></div>)}</div>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">02 · Validate capacity</p>
            <h2 className="mt-3 text-2xl font-semibold">A plan has to fit before it can be useful</h2>
            <div className="mt-5 grid gap-4 sm:grid-cols-3">
              <div className="surface p-5"><Clock3 className="h-5 w-5 text-accent" /><h3 className="mt-3 font-semibold">Availability</h3><p className="mt-2 text-sm leading-6 text-muted">09:30–18:30 working window, protected lunch, transition buffers, and a daily focus limit.</p></div>
              <div className="surface p-5"><Database className="h-5 w-5 text-accent" /><h3 className="mt-3 font-semibold">Calendar reality</h3><p className="mt-2 text-sm leading-6 text-muted">Fixed events reduce capacity. Cached or degraded calendar states remain visible instead of being silently ignored.</p></div>
              <div className="surface p-5"><Workflow className="h-5 w-5 text-accent" /><h3 className="mt-3 font-semibold">Dependencies</h3><p className="mt-2 text-sm leading-6 text-muted">Blocked work is not scheduled as executable focus merely because it has a deadline.</p></div>
            </div>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">03 · Explain the plan</p>
            <h2 className="mt-3 text-2xl font-semibold">The recommendation is inspectable</h2>
            <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_0.9fr]">
              <div className="surface p-6"><h3 className="font-semibold">Why this next action?</h3><ul className="mt-4 space-y-3 text-sm leading-6 text-muted"><li>• It has a near deadline and a credible 60-minute estimate.</li><li>• It fits before the fixed team event.</li><li>• The slide work is uncertain and dependency-blocked.</li><li>• Deferring the database assignment preserves today’s focus limit.</li></ul></div>
              <div className="surface p-6"><h3 className="font-semibold">What the system does not do</h3><ul className="mt-4 space-y-3 text-sm leading-6 text-muted"><li>• It does not silently move calendar events.</li><li>• It does not turn inferred context into fact.</li><li>• It does not persist an AI-generated plan until it passes validation and approval.</li></ul></div>
            </div>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">04 · Focus</p>
            <h2 className="mt-3 text-2xl font-semibold">Execution stays connected to the plan</h2>
            <div className="mt-5 surface p-6"><div className="flex items-start gap-4"><Focus className="mt-0.5 h-5 w-5 shrink-0 text-accent" /><div><h3 className="font-semibold">Authentication regression fix · 60 minutes</h3><p className="mt-2 text-sm leading-6 text-muted">Start, pause, resume, complete, or stop. Completion can record actual time, partial progress, energy, and a concise reflection so future plans are grounded in what really happened.</p></div></div></div>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">05 · Recover</p>
            <h2 className="mt-3 text-2xl font-semibold">When the day changes, recovery is constrained too</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-muted">Suppose the focus block is interrupted after 20 minutes and another meeting begins in 30 minutes. Continuing the remaining 40 minutes is no longer feasible. ChronOS diagnoses the disruption and offers bounded options instead of pretending the original plan still works.</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">{recoveryOptions.map(([title, text]) => <div key={title} className="surface p-5"><h3 className="font-semibold">{title}</h3><p className="mt-2 text-sm leading-6 text-muted">{text}</p></div>)}</div>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">06 · Context and provenance</p>
            <h2 className="mt-3 text-2xl font-semibold">Recommendations can cite what influenced them</h2>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <div className="surface p-5"><FileText className="h-5 w-5 text-accent" /><h3 className="mt-3 font-semibold">Project context</h3><p className="mt-2 text-sm leading-6 text-muted">“Production readiness requires stable authentication, verified rollback, deployment documentation, and responsive onboarding.” ChronOS can retrieve this as project context and show the source when it materially affects planning.</p></div>
              <div className="surface p-5"><ShieldCheck className="h-5 w-5 text-accent" /><h3 className="mt-3 font-semibold">Confirmed preference</h3><p className="mt-2 text-sm leading-6 text-muted">“I prefer 45-minute focus blocks and do not want important work immediately after meetings.” Explicit preferences outrank inferred patterns and remain editable.</p></div>
            </div>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">07 · External context</p>
            <h2 className="mt-3 text-2xl font-semibold">Integrations provide context before they provide control</h2>
            <p className="mt-3 text-sm leading-7 text-muted">Calendar, email, project, note, and task integrations normalize external information into attributed context and Inbox proposals. External content remains untrusted. Read access and proposal generation are separate from write authority, and external mutations remain explicit-approval operations.</p>
          </section>

          <section className="mt-12 border-t border-line pt-8">
            <p className="eyebrow">08 · Reliability</p>
            <h2 className="mt-3 text-2xl font-semibold">The system is designed to degrade instead of collapse</h2>
            <div className="mt-5 space-y-3 text-sm leading-7 text-muted"><p>If Groq is unavailable, deterministic planning state still loads. If retrieval fails, planning can continue from structured project and calendar data. If calendar data is stale, the source and confidence state remain visible. Provider retries and quotas are bounded before external calls can spiral.</p><p>Atomic database functions protect multi-write actions from partial completion, while RLS and ownership constraints keep one user’s plans, memory, context, integrations, and approvals isolated from another user.</p></div>
          </section>

          <div className="mt-12 flex flex-col items-center justify-between gap-4 rounded-2xl bg-ink p-6 text-white sm:flex-row"><div><h2 className="text-lg font-semibold">Try the same loop with your commitments</h2><p className="mt-1 text-sm text-white/70">Capture, review, plan, focus, and recover with clear approval boundaries.</p></div><Link className="inline-flex items-center rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-ink" to="/signup">Create an account<ArrowRight className="ml-2 h-4 w-4" /></Link></div>
        </div>
      </main>
    </div>
  );
}
