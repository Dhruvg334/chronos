import { CalendarRange, FolderKanban, Inbox, LogOut, Settings, SunMedium } from 'lucide-react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth/auth-context';

const primaryItems = [
  { label: 'Today', path: '/today', icon: SunMedium },
  { label: 'Inbox', path: '/inbox', icon: Inbox },
  { label: 'Plan', path: '/plan', icon: CalendarRange },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const { session, signOut } = useAuth();
  const queryClient = useQueryClient();

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="sticky top-0 z-20 border-b border-line bg-canvas/95 backdrop-blur-md">
        <div className="page-container grid h-16 grid-cols-[1fr_auto_1fr] items-center gap-3">
          <div className="justify-self-start">
            <Link to={session ? '/today' : '/'} className="brand-wordmark">Chron<span className="brand-os">OS</span></Link>
          </div>

          <nav aria-label="Primary navigation" className="hidden items-center rounded-xl border border-line bg-white p-1 md:flex">
            {primaryItems.map(({ label, path, icon: Icon }) => (
              <NavLink
                key={path}
                to={path}
                className={({ isActive }) => `relative inline-flex min-h-10 items-center justify-center gap-2 rounded-lg px-3.5 text-sm font-medium transition duration-200 ${isActive ? 'bg-[#F1F1EE] text-ink' : 'text-muted hover:bg-surface-subtle hover:text-ink'}`}
              >
                <Icon className="h-4 w-4" /><span>{label}</span>
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center justify-self-end gap-1">
            <Link to="/projects" className="button-ghost hidden lg:inline-flex"><FolderKanban className="mr-1.5 h-4 w-4" />Projects</Link>
            <Link to="/guide" className="button-ghost hidden xl:inline-flex">Guide</Link>
            <Link to="/settings" aria-label="Settings" className="icon-button"><Settings className="h-4 w-4" /></Link>
            <button className="icon-button" aria-label="Log out" onClick={async () => { await signOut(); queryClient.clear(); navigate('/'); }}><LogOut className="h-4 w-4" /></button>
          </div>
        </div>
      </header>

      <main className="page-container py-7 pb-28 md:py-10 md:pb-12">
        <div className="motion-enter">{children}</div>
      </main>

      <nav aria-label="Mobile navigation" className="fixed inset-x-3 bottom-3 z-30 flex justify-around rounded-2xl border border-line bg-white/95 p-1.5 shadow-float backdrop-blur md:hidden">
        {primaryItems.map(({ label, path, icon: Icon }) => (
          <NavLink key={path} to={path} className={({ isActive }) => `inline-flex min-w-[72px] flex-col items-center justify-center gap-1 rounded-xl px-3 py-2 text-[11px] font-medium transition ${isActive ? 'bg-[#F1F1EE] text-ink' : 'text-muted'}`}>
            <Icon className="h-4 w-4" /><span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
