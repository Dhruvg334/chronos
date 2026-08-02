import { ArrowRight, CalendarCheck, CheckCircle2, Inbox } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../components/auth/auth-context';

const steps = [
  { icon: Inbox, title: 'Capture', text: 'Put scattered commitments into one low-friction inbox.' },
  { icon: CalendarCheck, title: 'Shape the day', text: 'Fit meaningful work around calendar reality and buffers.' },
  { icon: CheckCircle2, title: 'Focus and adapt', text: 'Take the next action and repair the plan when reality changes.' },
];

export default function Landing() {
  const { session } = useAuth();
  return <div className="min-h-screen bg-canvas"><header className="page-container flex h-16 items-center justify-between"><Link to="/" className="text-xl font-semibold">Chron<span className="text-accent">OS</span></Link><nav className="flex items-center gap-4 text-sm font-medium"><Link to="/guide" className="text-muted hover:text-ink">Guide</Link>{session ? <Link className="button-primary" to="/today">Open Today</Link> : <><Link to="/login" className="hidden text-muted hover:text-ink sm:block">Log in</Link><Link className="button-primary" to="/signup">Sign up</Link></>}</nav></header>
    <main className="page-container py-16 sm:py-24"><section className="mx-auto max-w-4xl text-center"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent-strong">Personal planning and execution</p><h1 className="mx-auto mt-5 max-w-3xl text-4xl font-semibold leading-tight tracking-[-0.03em] sm:text-6xl">Turn scattered commitments into a realistic day.</h1><p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-muted">ChronOS finds a credible next action and quietly helps repair the plan when reality changes.</p><div className="mt-9 flex flex-col justify-center gap-3 sm:flex-row"><Link className="button-primary px-6 py-3" to={session ? '/today' : '/signup'}>{session ? 'Open Today' : 'Start planning'}<ArrowRight className="ml-2 h-4 w-4" /></Link><Link className="button-secondary px-6 py-3" to="/demo">Try guided demo</Link></div></section>
    <section aria-label="How it works" className="mx-auto mt-20 grid max-w-5xl gap-4 sm:grid-cols-3">{steps.map(({ icon: Icon, title, text }, index) => <article key={title} className="surface p-6 text-left"><div className="flex items-center justify-between"><span className="rounded-xl bg-accent-soft p-2 text-accent-strong"><Icon className="h-5 w-5" /></span><span className="text-xs font-semibold text-faint">0{index + 1}</span></div><h2 className="mt-5 text-lg font-semibold">{title}</h2><p className="mt-2 text-sm leading-6 text-muted">{text}</p></article>)}</section></main></div>;
}
