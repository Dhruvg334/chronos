import { ArrowRight, Github, ShieldCheck, Sparkles, TimerReset } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../components/auth/auth-context';

const navItems = [
  { href: '#product', label: 'Product' },
  { href: '#how-it-works', label: 'How it works' },
  { href: '#control', label: 'Safety' },
  { href: '/guide', label: 'About' },
];

const steps = [
  {
    number: '01',
    title: 'Capture the reality',
    text: 'Bring in commitments, projects, routines, and calendar constraints without turning capture into another planning task.',
  },
  {
    number: '02',
    title: 'Validate the plan',
    text: 'ChronOS checks capacity, protected time, dependencies, buffers, and deadlines before a suggestion can become your plan.',
  },
  {
    number: '03',
    title: 'Recover without chaos',
    text: 'When the day changes, get a small set of feasible options with the trade-offs made explicit. You remain in control.',
  },
];

function BrandMark({ className = '' }: { className?: string }) {
  return (
    <span className={`inline-flex h-10 w-10 items-center justify-center overflow-hidden rounded-[12px] bg-[#1f1f1c] ${className}`} aria-hidden="true">
      <img src="/chronos-mark.svg" alt="" className="h-7 w-7" />
    </span>
  );
}

export default function Landing() {
  const { session } = useAuth();
  const primaryDestination = session ? '/today' : '/signup';

  return (
    <div className="landing-page min-h-screen bg-[#faf9f7] text-ink">
      <header className="landing-nav-wrap">
        <nav className="landing-nav" aria-label="Landing navigation">
          <Link to="/" className="landing-brand" aria-label="ChronOS home">
            <BrandMark />
            <span>Chron<span className="text-accent">OS</span></span>
          </Link>

          <div className="landing-nav-links" aria-label="Product links">
            {navItems.map((item) => item.href.startsWith('/') ? (
              <Link key={item.label} to={item.href} className="landing-nav-link">{item.label}</Link>
            ) : (
              <a key={item.label} href={item.href} className="landing-nav-link">{item.label}</a>
            ))}
          </div>

          <div className="landing-nav-actions">
            <a
              className="landing-icon-link"
              href="https://github.com/Dhruvg334/ChronOS"
              target="_blank"
              rel="noreferrer"
              aria-label="ChronOS on GitHub"
            >
              <Github className="h-[18px] w-[18px]" />
            </a>
            {!session && <Link to="/login" className="landing-login-link">Log in</Link>}
            <Link to={primaryDestination} className="landing-cta landing-cta-compact">
              {session ? 'Open ChronOS' : 'Start planning'}
            </Link>
          </div>
        </nav>
      </header>

      <main>
        <section id="product" className="landing-hero" aria-labelledby="landing-title">
          <div className="landing-ambient landing-ambient-left" aria-hidden="true" />
          <div className="landing-ambient landing-ambient-right" aria-hidden="true" />

          <div className="landing-hero-inner">
            <div className="landing-kicker motion-pop">
              <span className="landing-kicker-dot" aria-hidden="true" />
              Capacity-aware planning, built around your approval
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </div>

            <h1 id="landing-title" className="landing-title motion-enter">
              Make plans that survive<br />
              <span className="landing-title-accent">the real day.</span>
            </h1>

            <p className="landing-subtitle motion-enter">
              ChronOS turns commitments, project outcomes, routines, and calendar constraints into a realistic plan — then helps you recover when reality changes.
            </p>

            <div className="landing-hero-actions motion-enter">
              <Link to={primaryDestination} className="landing-cta">
                {session ? 'Open your day' : 'Start planning'}
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
              <Link to="/demo" className="landing-secondary-cta">
                See a sample day
              </Link>
            </div>

            <div className="landing-proof motion-enter" aria-label="ChronOS principles">
              <span><span className="landing-check" aria-hidden="true">✓</span> Capacity-aware</span>
              <span className="landing-proof-separator" aria-hidden="true">•</span>
              <span><span className="landing-check" aria-hidden="true">✓</span> Approval-first</span>
              <span className="landing-proof-separator" aria-hidden="true">•</span>
              <span><span className="landing-check" aria-hidden="true">✓</span> Adaptive recovery</span>
            </div>

            <div className="landing-plan-ribbon" aria-label="Example validated day">
              <div className="landing-ribbon-meta">
                <span>Thursday</span>
                <strong>5h 10m usable</strong>
              </div>
              <div className="landing-ribbon-track">
                <div className="landing-ribbon-block landing-ribbon-focus" style={{ flex: 4.1 }}>
                  <span>09:30</span>
                  <strong>Authentication regression fix</strong>
                </div>
                <div className="landing-ribbon-block landing-ribbon-event" style={{ flex: 2.15 }}>
                  <span>11:00</span>
                  <strong>Team sync</strong>
                </div>
                <div className="landing-ribbon-block landing-ribbon-work" style={{ flex: 2.5 }}>
                  <span>12:10</span>
                  <strong>Deployment review</strong>
                </div>
                <div className="landing-ribbon-buffer" style={{ flex: 1.15 }}>
                  <span>Buffer</span>
                </div>
              </div>
              <div className="landing-ribbon-note">
                <span>Validated against calendar, focus limit, transitions, and protected time.</span>
                <span className="landing-workable">Workable</span>
              </div>
            </div>
          </div>
        </section>

        <section id="how-it-works" className="landing-section landing-how" aria-labelledby="how-title">
          <div className="landing-section-inner">
            <div className="landing-section-heading">
              <p className="landing-section-eyebrow">How it works</p>
              <h2 id="how-title">Planning is a constraint problem.<br />ChronOS treats it like one.</h2>
              <p>AI helps with interpretation and trade-offs. Deterministic rules decide whether a plan can actually fit.</p>
            </div>

            <div className="landing-steps">
              {steps.map((step) => (
                <article key={step.number} className="landing-step">
                  <div className="landing-step-number">{step.number}</div>
                  <h3>{step.title}</h3>
                  <p>{step.text}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="control" className="landing-section landing-control" aria-labelledby="control-title">
          <div className="landing-control-inner">
            <div className="landing-control-copy">
              <p className="landing-section-eyebrow landing-section-eyebrow-dark">Designed for control</p>
              <h2 id="control-title">Helpful enough to adapt.<br />Bounded enough to trust.</h2>
              <p>
                ChronOS can explain a plan, surface context, and propose recovery. It cannot quietly rewrite your priorities or turn an external suggestion into an action without the right approval boundary.
              </p>
              <Link to="/guide" className="landing-control-link">
                Read how ChronOS is designed <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="landing-control-grid">
              <div className="landing-control-item">
                <ShieldCheck className="h-5 w-5" />
                <div>
                  <strong>Approval-first actions</strong>
                  <span>Consequential changes stay visible before they happen.</span>
                </div>
              </div>
              <div className="landing-control-item">
                <TimerReset className="h-5 w-5" />
                <div>
                  <strong>Graceful recovery</strong>
                  <span>Missed work becomes a decision, not a silent reshuffle.</span>
                </div>
              </div>
              <div className="landing-control-item">
                <Sparkles className="h-5 w-5" />
                <div>
                  <strong>Attributable context</strong>
                  <span>Recommendations can show which memory, note, or constraint influenced them.</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <Link to="/" className="landing-brand landing-brand-footer" aria-label="ChronOS home">
            <BrandMark className="h-8 w-8 rounded-[10px]" />
            <span>Chron<span className="text-accent">OS</span></span>
          </Link>
          <p>A personal execution system for plans that have to survive reality.</p>
          <div className="landing-footer-links">
            <Link to="/guide">About</Link>
            <Link to="/demo">Demo</Link>
            <a href="https://github.com/Dhruvg334/ChronOS" target="_blank" rel="noreferrer">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
