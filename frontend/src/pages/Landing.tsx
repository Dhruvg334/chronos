import { ArrowRight, Check, ShieldCheck, Sparkles, TimerReset } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../components/auth/auth-context';

const flow = [
  ['01', 'Capture the real work', 'Commitments, outcomes, routines, events, dependencies, and uncertainty enter one planning context.'],
  ['02', 'Validate what fits', 'Availability, protected time, buffers, deadlines, focus limits, and blocked work are checked before a plan is accepted.'],
  ['03', 'Recover deliberately', 'When reality changes, ChronOS proposes a small set of feasible alternatives and leaves consequential changes behind approval.'],
];

const trust = [
  [ShieldCheck, 'Approval-first', 'Important changes stay visible before they happen.'],
  [TimerReset, 'Recovery-aware', 'A broken plan becomes a decision, not a silent reshuffle.'],
  [Sparkles, 'Attributable context', 'Relevant memory and knowledge remain inspectable at the source.'],
] as const;

function RepositoryMark() {
  return (
    <svg viewBox="0 0 24 24" className="h-[17px] w-[17px]" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="7" cy="6" r="2" />
      <circle cx="17" cy="18" r="2" />
      <circle cx="7" cy="18" r="2" />
      <path d="M7 8v8" />
      <path d="M9 6h3a5 5 0 0 1 5 5v5" />
    </svg>
  );
}

function ChronOSMark({ size = 38 }: { size?: number }) {
  return (
    <span className="inline-grid shrink-0 place-items-center rounded-[11px] bg-accent shadow-[0_8px_24px_rgba(198,106,30,0.18)]" style={{ width: size, height: size }} aria-hidden="true">
      <img src="/chronos-mark.svg" alt="" className="h-[72%] w-[72%]" />
    </span>
  );
}

function DayPreview() {
  return (
    <div className="w-full max-w-[860px] overflow-hidden rounded-[22px] border border-[#E2DDD5] bg-white text-left shadow-[0_24px_70px_rgba(42,35,28,0.08)]">
      <div className="flex items-center justify-between gap-4 border-b border-line px-5 py-4 sm:px-6">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-faint">Thursday · 5h 10m usable</p>
          <p className="mt-1 text-[15px] font-semibold tracking-[-0.02em] text-ink">A workable day, not a perfect one</p>
        </div>
        <span className="rounded-full bg-success-soft px-2.5 py-1 text-[11px] font-semibold text-success">Validated</span>
      </div>

      <div className="grid md:grid-cols-[1.03fr_1px_0.97fr]">
        <div className="p-5 sm:p-6">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-faint">Next action</p>
          <h2 className="mt-2 text-xl font-semibold tracking-[-0.025em] text-ink">Authentication regression fix</h2>
          <p className="mt-1.5 text-sm text-muted">60 min · high impact · fits before team sync</p>

          <div className="mt-6 flex h-2 overflow-hidden rounded-full bg-[#EFEDE8]" aria-hidden="true">
            <span className="w-[47%] bg-accent" />
            <span className="w-[22%] bg-[#B8B5AE]" />
            <span className="w-[18%] bg-[#D8B993]" />
          </div>
          <div className="mt-2.5 flex justify-between text-[10px] font-medium text-faint"><span>Focus</span><span>Fixed events</span><span>Buffer kept</span></div>
        </div>

        <div className="hidden bg-line md:block" />

        <div className="p-5 sm:p-6">
          <div className="grid grid-cols-[52px_1fr] gap-y-4 text-sm">
            <span className="text-faint">09:30</span><div><p className="font-semibold text-ink">Deep work</p><p className="mt-0.5 text-xs text-muted">Authentication fix</p></div>
            <span className="text-faint">11:00</span><div><p className="font-semibold text-ink">Team sync</p><p className="mt-0.5 text-xs text-muted">Calendar · fixed</p></div>
            <span className="text-faint">12:10</span><div><p className="font-semibold text-ink">Deployment review</p><p className="mt-0.5 text-xs text-muted">25 min · batched</p></div>
          </div>
          <p className="mt-5 border-t border-line pt-4 text-xs leading-5 text-muted">Slides move to tomorrow because today exceeds capacity. Nothing changes without approval.</p>
        </div>
      </div>
    </div>
  );
}

export default function Landing() {
  const { session } = useAuth();
  const primaryDestination = session ? '/today' : '/signup';

  return (
    <div className="landing-v3 min-h-screen bg-[#FAFAF8] text-ink">
      <header className="border-b border-line/80 bg-[#FAFAF8]/95 backdrop-blur">
        <nav className="mx-auto flex h-[72px] w-full max-w-[1180px] items-center justify-between px-5 sm:px-7" aria-label="Landing navigation">
          <Link to="/" className="inline-flex items-center gap-3 no-underline" aria-label="ChronOS home">
            <ChronOSMark />
            <span className="text-[18px] font-semibold tracking-[-0.035em] text-ink">Chron<span className="text-accent">OS</span></span>
          </Link>

          <div className="hidden items-center gap-8 text-sm font-medium text-muted md:flex">
            <a href="#how" className="transition hover:text-ink">How it works</a>
            <a href="#principles" className="transition hover:text-ink">Principles</a>
            <Link to="/guide" className="transition hover:text-ink">About</Link>
          </div>

          <div className="flex items-center gap-2">
            <a href="https://github.com/Dhruvg334/ChronOS" target="_blank" rel="noreferrer" aria-label="ChronOS on GitHub" className="hidden h-10 w-10 items-center justify-center rounded-xl border border-line bg-white text-ink transition hover:border-[#D2D2CC] hover:bg-surface-subtle sm:inline-flex"><RepositoryMark /></a>
            {!session && <Link to="/login" className="hidden rounded-xl px-3 py-2 text-sm font-medium text-muted transition hover:text-ink sm:inline-flex">Log in</Link>}
            <Link to={primaryDestination} className="inline-flex min-h-10 items-center rounded-xl bg-accent px-4 text-sm font-semibold text-white transition hover:bg-accent-strong">
              {session ? 'Open ChronOS' : 'Get started'}
            </Link>
          </div>
        </nav>
      </header>

      <main>
        <section className="landing-v3-hero relative overflow-hidden border-b border-line/80">
          <div className="landing-v3-aura landing-v3-aura-left" aria-hidden="true" />
          <div className="landing-v3-aura landing-v3-aura-right" aria-hidden="true" />

          <div className="relative mx-auto flex w-full max-w-[1120px] flex-col items-center px-5 pb-16 pt-14 text-center sm:px-7 sm:pt-16 lg:pb-20 lg:pt-20">
            <div className="landing-v3-enter inline-flex items-center gap-2 rounded-full border border-[#E7DED5] bg-white/80 px-3 py-1.5 text-[12px] font-semibold text-[#665E57] shadow-[0_6px_20px_rgba(45,38,31,0.04)]">
              <span className="grid h-5 w-5 place-items-center rounded-full bg-accent-soft text-accent-strong"><Check className="h-3 w-3" strokeWidth={2.8} /></span>
              A personal execution system for realistic days
            </div>

            <h1 aria-label="Plan the day you can actually execute." className="landing-v3-enter landing-v3-delay-1 mt-7 max-w-[980px] text-balance text-[clamp(3.25rem,6.7vw,6.5rem)] font-[620] leading-[0.93] tracking-[-0.058em] text-[#11110F]">
              Plan the day you can
              <span className="block text-accent">actually execute.</span>
            </h1>

            <p className="landing-v3-enter landing-v3-delay-2 mt-6 max-w-[700px] text-balance text-[clamp(1rem,1.25vw,1.16rem)] leading-8 text-muted">
              ChronOS turns commitments, projects, routines, and calendar constraints into a plan that fits — then helps you recover when reality changes.
            </p>

            <div className="landing-v3-enter landing-v3-delay-3 mt-7 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
              <Link to={primaryDestination} className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-accent px-5 text-sm font-semibold text-white shadow-[0_12px_28px_rgba(198,106,30,0.18)] transition hover:-translate-y-0.5 hover:bg-accent-strong">
                {session ? 'Open your day' : 'Start planning'} <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="landing-v3-enter landing-v3-delay-4 mt-6 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-[12px] font-medium text-[#77736D]" aria-label="ChronOS principles">
              {['Capacity-aware', 'Approval-first', 'Adaptive recovery'].map((item) => <span key={item} className="inline-flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-accent" aria-hidden="true" />{item}</span>)}
            </div>

            <div className="landing-v3-enter landing-v3-delay-5 mt-10 w-full">
              <div className="grid items-center gap-4 lg:grid-cols-[150px_minmax(0,860px)_150px] lg:justify-center lg:gap-5">
                <div className="order-2 flex justify-center lg:order-1 lg:justify-end">
                  <Link to="/demo" className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-line bg-white px-4 text-sm font-semibold text-ink shadow-[0_8px_20px_rgba(40,34,27,0.04)] transition hover:-translate-y-0.5 hover:bg-surface-subtle">
                    Sample day
                  </Link>
                </div>

                <div className="order-1 lg:order-2"><DayPreview /></div>

                <div className="order-3 flex justify-center lg:justify-start">
                  <Link to="/guide" className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-line bg-white px-4 text-sm font-semibold text-ink shadow-[0_8px_20px_rgba(40,34,27,0.04)] transition hover:-translate-y-0.5 hover:bg-surface-subtle">
                    About ChronOS
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="how" className="border-b border-line bg-white py-20 sm:py-24">
          <div className="mx-auto w-full max-w-[1120px] px-5 sm:px-7">
            <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:gap-20">
              <div>
                <p className="eyebrow">How it works</p>
                <h2 className="mt-3 max-w-[520px] text-[clamp(2.1rem,4vw,3.5rem)] font-semibold leading-[1.03] tracking-[-0.05em] text-ink">Planning is a constraint problem. ChronOS treats it like one.</h2>
                <p className="mt-5 max-w-[520px] text-base leading-7 text-muted">AI helps interpret ambiguity and explain trade-offs. Deterministic validation decides whether a plan can actually fit.</p>
              </div>

              <div className="divide-y divide-line border-y border-line">
                {flow.map(([step, title, text]) => <article key={step} className="grid gap-4 py-6 sm:grid-cols-[54px_1fr]"><span className="text-xs font-semibold text-accent-strong">{step}</span><div><h3 className="text-base font-semibold text-ink">{title}</h3><p className="mt-2 text-sm leading-6 text-muted">{text}</p></div></article>)}
              </div>
            </div>
          </div>
        </section>

        <section id="principles" className="bg-[#FAFAF8] py-20 sm:py-24">
          <div className="mx-auto w-full max-w-[1120px] px-5 sm:px-7">
            <div className="grid gap-10 lg:grid-cols-[0.86fr_1.14fr] lg:gap-20">
              <div>
                <p className="eyebrow">Designed for control</p>
                <h2 className="mt-3 max-w-[520px] text-[clamp(2.1rem,4vw,3.5rem)] font-semibold leading-[1.03] tracking-[-0.05em] text-ink">Helpful enough to adapt. Bounded enough to trust.</h2>
                <p className="mt-5 max-w-[540px] text-sm leading-7 text-muted">ChronOS can interpret, retrieve context, and propose. Feasibility rules, permissions, and approval boundaries decide what can actually change.</p>
                <Link to="/guide" className="mt-7 inline-flex items-center gap-2 text-sm font-semibold text-accent-strong">Read the design approach <ArrowRight className="h-4 w-4" /></Link>
              </div>

              <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
                {trust.map(([Icon, title, text]) => <article key={title} className="grid grid-cols-[36px_1fr] gap-4 rounded-2xl border border-line bg-white p-5 shadow-[0_8px_24px_rgba(42,35,28,0.035)]"><span className="grid h-9 w-9 place-items-center rounded-xl bg-accent-soft text-accent-strong"><Icon className="h-4.5 w-4.5" /></span><div><h3 className="text-sm font-semibold text-ink">{title}</h3><p className="mt-1.5 text-xs leading-5 text-muted">{text}</p></div></article>)}
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-line bg-white py-7">
        <div className="mx-auto flex w-full max-w-[1120px] flex-col items-center justify-between gap-4 px-5 text-xs text-faint sm:flex-row sm:px-7">
          <div className="inline-flex items-center gap-2"><ChronOSMark size={28} /><span className="font-semibold text-ink">Chron<span className="text-accent">OS</span></span></div>
          <p>A personal execution system for plans that have to survive reality.</p>
          <div className="flex gap-5"><Link to="/guide">About</Link><Link to="/demo">Demo</Link><a href="https://github.com/Dhruvg334/ChronOS" target="_blank" rel="noreferrer">GitHub</a></div>
        </div>
      </footer>
    </div>
  );
}
