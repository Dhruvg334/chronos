import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2, Clock, ShieldCheck, Sparkles } from 'lucide-react';
import { demoCommitments, demoSuggestions, riskClasses, riskLabels } from '../data/demoScenario';

export default function Demo() {
  const critical = demoCommitments.find((item) => item.risk === 'rescue_required') ?? demoCommitments[0];

  return (
    <div className="min-h-screen bg-warm-ivory px-4 py-6 text-text-primary sm:px-6 lg:px-8">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between py-2">
        <Link to="/" className="text-2xl font-extrabold tracking-tight">
          Chron<span className="text-accent-amber">OS</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm font-semibold">
          <Link to="/about" className="text-text-secondary hover:text-text-primary">Guide</Link>
          <Link to="/login" className="text-text-secondary hover:text-text-primary">Log in</Link>
          <Link to="/signup" className="rounded-xl bg-accent-amber px-4 py-2 text-white shadow-sm hover:bg-accent-terracotta">
            Sign up
          </Link>
        </nav>
      </header>

      <main className="mx-auto mt-8 w-full max-w-6xl rounded-3xl border border-warm-border bg-white p-6 shadow-sm md:p-10">
        <section className="grid gap-8 lg:grid-cols-[1fr_360px] lg:items-start">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-warm-border bg-warm-cream px-3 py-1 text-xs font-bold uppercase tracking-wide text-accent-copper">
              <Sparkles className="h-3.5 w-3.5" /> Public product demo
            </div>
            <h1 className="max-w-3xl text-4xl font-extrabold leading-tight tracking-tight md:text-5xl">
              See how ChronOS turns a messy deadline day into a recovery plan.
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-text-secondary">
              This demo is view-only and does not require an account. It shows the core loop: commitments, capacity, agent suggestions, and human approval.
            </p>
          </div>

          <div className="rounded-2xl border border-warm-border bg-warm-cream p-5">
            <h2 className="mb-3 text-lg font-bold">Today’s command brief</h2>
            <div className="space-y-4 text-sm">
              <div className="rounded-xl border border-warm-border bg-white p-4">
                <p className="text-xs font-bold uppercase tracking-wide text-text-muted">Time health</p>
                <p className="mt-1 text-xl font-extrabold text-risk-critical">Rescue required</p>
                <p className="mt-1 text-text-secondary">{critical.title} needs intervention before new work starts.</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-warm-border bg-white p-4">
                  <p className="text-xs font-bold uppercase tracking-wide text-text-muted">Available</p>
                  <p className="mt-1 text-xl font-extrabold">{critical.availableMinutes}m</p>
                </div>
                <div className="rounded-xl border border-warm-border bg-white p-4">
                  <p className="text-xs font-bold uppercase tracking-wide text-text-muted">Needed</p>
                  <p className="mt-1 text-xl font-extrabold">{critical.remainingMinutes}m</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-10 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-2xl border border-warm-border bg-warm-cream p-5">
            <div className="mb-4 flex items-center justify-between gap-4">
              <h2 className="text-xl font-bold">Demo commitments</h2>
              <span className="text-sm text-text-muted">No login needed</span>
            </div>
            <div className="space-y-3">
              {demoCommitments.map((item) => (
                <article key={item.title} className="rounded-xl border border-warm-border bg-white p-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="font-bold">{item.title}</h3>
                      <p className="mt-1 text-sm leading-6 text-text-secondary">{item.description}</p>
                    </div>
                    <span className={`w-fit shrink-0 rounded-lg px-2 py-1 text-[10px] font-bold uppercase tracking-wide ${riskClasses[item.risk]}`}>
                      {riskLabels[item.risk]}
                    </span>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-4 text-sm text-text-muted">
                    <span className="flex items-center gap-1.5"><Clock className="h-4 w-4" /> {item.deadline}</span>
                    <span>{item.remainingMinutes}m remaining</span>
                    <span>{item.availableMinutes}m usable capacity</span>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-warm-border bg-white p-5">
            <div className="mb-4 flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-risk-stable" />
              <h2 className="text-xl font-bold">What the agents propose</h2>
            </div>
            <div className="space-y-3">
              {demoSuggestions.map((item) => (
                <article key={`${item.agent}-${item.title}`} className="rounded-xl border border-warm-border bg-warm-cream p-4">
                  <p className="text-xs font-bold uppercase tracking-wide text-accent-copper">{item.agent}</p>
                  <h3 className="mt-1 font-bold">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-text-secondary">{item.reason}</p>
                  <p className="mt-3 flex items-start gap-2 text-sm font-semibold text-text-primary">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 text-risk-stable" /> {item.action}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-8 rounded-2xl border border-warm-border bg-warm-cream p-5">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-xl font-bold">Ready to try it with your own commitments?</h2>
              <p className="mt-1 text-sm text-text-secondary">Create an account to run live analysis, connect calendar availability, and approve your own recovery actions.</p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Link to="/signup" className="inline-flex items-center justify-center gap-2 rounded-xl bg-accent-amber px-5 py-3 text-sm font-bold text-white shadow-sm hover:bg-accent-terracotta">
                Start with ChronOS <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/about" className="inline-flex items-center justify-center rounded-xl border border-warm-border bg-white px-5 py-3 text-sm font-bold text-text-primary hover:bg-warm-ivory">
                Read the guide
              </Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
