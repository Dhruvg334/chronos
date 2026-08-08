import { ArrowRight, Check, ShieldCheck, Sparkles, TimerReset } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../components/auth/auth-context';

const principles = [
  'Capacity-aware',
  'Approval-first',
  'Adaptive recovery',
];

const flow = [
  {
    step: '01',
    title: 'Capture what is real',
    text: 'Commitments, outcomes, routines, dependencies, and calendar constraints enter one planning context.',
  },
  {
    step: '02',
    title: 'Build only what fits',
    text: 'ChronOS validates availability, buffers, protected time, focus limits, deadlines, and blocked work before a plan can be accepted.',
  },
  {
    step: '03',
    title: 'Recover without chaos',
    text: 'When the day changes, ChronOS proposes a small set of feasible alternatives and keeps consequential changes behind approval.',
  },
];


function RepositoryMark() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-[17px] w-[17px]"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
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
    <span
      className="inline-grid shrink-0 place-items-center rounded-[11px] bg-accent shadow-[0_8px_24px_rgba(198,106,30,0.18)]"
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <img src="/chronos-mark.svg" alt="" className="h-[72%] w-[72%]" />
    </span>
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
            <a href="#trust" className="transition hover:text-ink">Design principles</a>
            <Link to="/guide" className="transition hover:text-ink">About</Link>
          </div>

          <div className="flex items-center gap-2">
            <a
              href="https://github.com/Dhruvg334/ChronOS"
              target="_blank"
              rel="noreferrer"
              aria-label="ChronOS on GitHub"
              className="hidden h-10 w-10 items-center justify-center rounded-xl border border-line bg-white text-ink transition hover:border-[#D2D2CC] hover:bg-surface-subtle sm:inline-flex"
            >
              <RepositoryMark />
            </a>
            {!session && <Link to="/login" className="hidden rounded-xl px-3 py-2 text-sm font-medium text-muted transition hover:text-ink sm:inline-flex">Log in</Link>}
            <Link to={primaryDestination} className="inline-flex min-h-10 items-center rounded-xl bg-accent px-4 text-sm font-semibold text-white transition hover:bg-accent-strong">
              {session ? 'Open ChronOS' : 'Start planning'}
            </Link>
          </div>
        </nav>
      </header>

      <main>
        <section className="landing-v3-hero relative overflow-hidden border-b border-line/80">
          <div className="landing-v3-aura landing-v3-aura-left" aria-hidden="true" />
          <div className="landing-v3-aura landing-v3-aura-right" aria-hidden="true" />

          <div className="relative mx-auto flex min-h-[calc(100svh-72px)] w-full max-w-[1120px] flex-col items-center justify-center px-5 py-14 text-center sm:px-7 lg:min-h-[690px]">
            <div className="landing-v3-enter inline-flex items-center gap-2 rounded-full border border-[#E7DED5] bg-white/80 px-3 py-1.5 text-[12px] font-semibold text-[#665E57] shadow-[0_6px_20px_rgba(45,38,31,0.04)]">
              <span className="grid h-5 w-5 place-items-center rounded-full bg-accent-soft text-accent-strong"><Check className="h-3 w-3" strokeWidth={2.8} /></span>
              A personal execution system for realistic days
            </div>

            <h1
              aria-label="Plan the day you can actually execute."
              className="landing-v3-enter landing-v3-delay-1 mt-8 max-w-[980px] text-balance text-[clamp(3.35rem,7vw,6.75rem)] font-[620] leading-[0.92] tracking-[-0.06em] text-[#11110F]"
            >
              Plan the day you can
              <span className="block text-accent">actually execute.</span>
            </h1>

            <p className="landing-v3-enter landing-v3-delay-2 mt-7 max-w-[720px] text-balance text-[clamp(1rem,1.35vw,1.2rem)] leading-8 text-muted">
              ChronOS turns commitments, projects, routines, and calendar constraints into a plan that fits — then helps you recover when reality changes.
            </p>

            <div className="landing-v3-enter landing-v3-delay-3 mt-8 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
              <Link to={primaryDestination} className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-accent px-5 text-sm font-semibold text-white shadow-[0_12px_28px_rgba(198,106,30,0.2)] transition hover:-translate-y-0.5 hover:bg-accent-strong">
                {session ? 'Open your day' : 'Start planning'}
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/demo" className="inline-flex min-h-12 items-center justify-center rounded-xl border border-line bg-white px-5 text-sm font-semibold text-ink transition hover:-translate-y-0.5 hover:bg-surface-subtle">
                See a sample day
              </Link>
            </div>

            <div className="landing-v3-enter landing-v3-delay-4 mt-7 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-[12px] font-medium text-[#77736D]" aria-label="ChronOS principles">
              {principles.map((item) => (
                <span key={item} className="inline-flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent" aria-hidden="true" />
                  {item}
                </span>
              ))}
            </div>

            <div className="landing-v3-enter landing-v3-delay-5 mt-10 w-full max-w-[900px] overflow-hidden rounded-[20px] border border-[#E4DED5] bg-white/90 text-left shadow-[0_22px_60px_rgba(40,34,27,0.08)]">
              <div className="flex items-center justify-between gap-4 border-b border-line px-5 py-3.5">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-faint">Thursday · 5h 10m usable</p>
                  <p className="mt-1 text-sm font-semibold text-ink">A workable day, not a perfect one</p>
                </div>
                <span className="rounded-full bg-success-soft px-2.5 py-1 text-[11px] font-semibold text-success">Validated</span>
              </div>

              <div className="grid gap-0 md:grid-cols-[1fr_1px_1.18fr]">
                <div className="p-5">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-faint">Next action</p>
                  <h2 className="mt-2 text-lg font-semibold tracking-[-0.02em] text-ink">Authentication regression fix</h2>
                  <p className="mt-1 text-sm text-muted">60 min · high impact · fits before team sync</p>
                  <div className="mt-5 flex h-2 overflow-hidden rounded-full bg-[#EFEDE8]" aria-hidden="true">
                    <span className="w-[46%] bg-accent" />
                    <span className="w-[21%] bg-[#B8B5AE]" />
                    <span className="w-[18%] bg-[#D7B58F]" />
                  </div>
                  <div className="mt-2 flex justify-between text-[10px] font-medium text-faint"><span>Focus</span><span>Meetings</span><span>Buffer kept</span></div>
                </div>
                <div className="hidden bg-line md:block" />
                <div className="grid grid-cols-3 gap-3 p-5">
                  <div><p className="text-[11px] text-faint">09:30</p><p className="mt-1 text-sm font-semibold text-ink">Deep work</p></div>
                  <div><p className="text-[11px] text-faint">11:00</p><p className="mt-1 text-sm font-semibold text-ink">Team sync</p></div>
                  <div><p className="text-[11px] text-faint">12:10</p><p className="mt-1 text-sm font-semibold text-ink">Review</p></div>
                  <p className="col-span-3 mt-2 border-t border-line pt-3 text-xs leading-5 text-muted">Slides move to tomorrow because the original day exceeds capacity. Nothing changes without approval.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="how" className="border-b border-line bg-white py-20 sm:py-24">
          <div className="mx-auto w-full max-w-[1120px] px-5 sm:px-7">
            <div className="grid gap-10 lg:grid-cols-[0.95fr_1.05fr] lg:gap-20">
              <div>
                <p className="eyebrow">How it works</p>
                <h2 className="mt-3 max-w-[520px] text-[clamp(2.2rem,4vw,3.7rem)] font-semibold leading-[1.02] tracking-[-0.05em] text-ink">Planning is a constraint problem. ChronOS treats it like one.</h2>
                <p className="mt-5 max-w-[520px] text-base leading-7 text-muted">Language models help interpret ambiguity and explain trade-offs. Deterministic validation decides whether the plan can actually fit.</p>
              </div>

              <div className="divide-y divide-line border-y border-line">
                {flow.map((item) => (
                  <article key={item.step} className="grid gap-4 py-6 sm:grid-cols-[54px_1fr]">
                    <span className="text-xs font-semibold text-accent-strong">{item.step}</span>
                    <div><h3 className="text-base font-semibold text-ink">{item.title}</h3><p className="mt-2 text-sm leading-6 text-muted">{item.text}</p></div>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="trust" className="bg-[#20201E] py-20 text-white">
          <div className="mx-auto grid w-full max-w-[1120px] gap-10 px-5 sm:px-7 lg:grid-cols-[1fr_1fr] lg:gap-20">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#E7A36F]">Designed for control</p>
              <h2 className="mt-3 max-w-[520px] text-[clamp(2.2rem,4vw,3.5rem)] font-semibold leading-[1.03] tracking-[-0.05em]">Helpful enough to adapt. Bounded enough to trust.</h2>
              <p className="mt-5 max-w-[540px] text-sm leading-7 text-white/60">ChronOS can interpret, retrieve context, and propose. Feasibility rules, permissions, and approval boundaries decide what can actually change.</p>
              <Link to="/guide" className="mt-7 inline-flex items-center gap-2 text-sm font-semibold text-[#F0A56B]">Read the design approach <ArrowRight className="h-4 w-4" /></Link>
            </div>

            <div className="divide-y divide-white/10 border-y border-white/10">
              {[
                [ShieldCheck, 'Approval-first actions', 'Consequential changes stay visible before they happen.'],
                [TimerReset, 'Graceful recovery', 'A missed block becomes a decision, not a silent reshuffle.'],
                [Sparkles, 'Attributable context', 'Relevant memory and knowledge can be inspected at the source.'],
              ].map(([Icon, title, text]) => {
                const C = Icon as typeof ShieldCheck;
                return <div key={String(title)} className="grid grid-cols-[28px_1fr] gap-4 py-5"><C className="mt-0.5 h-5 w-5 text-[#F0A56B]" /><div><h3 className="text-sm font-semibold">{String(title)}</h3><p className="mt-1 text-xs leading-5 text-white/55">{String(text)}</p></div></div>;
              })}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-line bg-[#FAFAF8] py-7">
        <div className="mx-auto flex w-full max-w-[1120px] flex-col items-center justify-between gap-4 px-5 text-xs text-faint sm:flex-row sm:px-7">
          <div className="inline-flex items-center gap-2"><ChronOSMark size={28} /><span className="font-semibold text-ink">Chron<span className="text-accent">OS</span></span></div>
          <p>A personal execution system for plans that have to survive reality.</p>
          <div className="flex gap-5"><Link to="/guide">About</Link><Link to="/demo">Demo</Link><a href="https://github.com/Dhruvg334/ChronOS" target="_blank" rel="noreferrer">GitHub</a></div>
        </div>
      </footer>
    </div>
  );
}
