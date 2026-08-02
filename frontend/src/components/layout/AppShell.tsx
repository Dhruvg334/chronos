import { CalendarRange, Inbox, LogOut, Settings, SunMedium } from 'lucide-react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/auth-context';

const primaryItems = [
  { label: 'Today', path: '/today', icon: SunMedium },
  { label: 'Inbox', path: '/inbox', icon: Inbox },
  { label: 'Plan', path: '/plan', icon: CalendarRange },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const { session, signOut } = useAuth();

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="sticky top-0 z-20 border-b border-line bg-canvas/95 backdrop-blur-sm">
        <div className="page-container flex h-16 items-center justify-between gap-4">
          <Link to={session ? '/today' : '/'} className="text-xl font-semibold tracking-tight">Chron<span className="text-accent">OS</span></Link>
          <nav aria-label="Primary navigation" className="fixed inset-x-3 bottom-3 z-30 flex justify-around rounded-2xl border border-line bg-surface p-2 shadow-soft md:static md:inset-auto md:justify-start md:rounded-xl md:shadow-none">
            {primaryItems.map(({ label, path, icon: Icon }) => (
              <NavLink key={path} to={path} className={({ isActive }) => `inline-flex min-w-16 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${isActive ? 'bg-accent-soft text-accent-strong' : 'text-muted hover:bg-surface-subtle hover:text-ink'}`}>
                <Icon className="h-4 w-4" /><span>{label}</span>
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            <Link to="/guide" className="hidden text-sm font-medium text-muted hover:text-ink sm:block">Guide</Link>
            <Link to="/settings" aria-label="Settings" className="icon-button"><Settings className="h-4 w-4" /></Link>
            <button className="icon-button" aria-label="Log out" onClick={async () => { await signOut(); navigate('/'); }}><LogOut className="h-4 w-4" /></button>
          </div>
        </div>
      </header>
      <main className="page-container py-6 pb-28 md:py-10 md:pb-12">{children}</main>
    </div>
  );
}
