import { Link, useLocation } from 'react-router-dom';

interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const location = useLocation();

  const navItems = [
    { label: 'Command', path: '/command' },
    { label: 'Inbox', path: '/inbox' },
    { label: 'Calendar', path: '/calendar' },
    { label: 'Rescue', path: '/rescue' },
    { label: 'Reflection', path: '/reflection' },
    { label: 'Settings', path: '/settings' },
  ];

  return (
    <div className="min-h-screen bg-warm-ivory text-text-primary flex flex-col font-sans">
      {/* Centered App Header & Navbar */}
      <header className="py-6 px-8 flex justify-between items-center max-w-7xl w-full mx-auto">
        <Link to="/" className="text-2xl font-bold tracking-tight">
          Chron<span className="text-accent-amber">OS</span>
        </Link>
        
        {/* Oval Navbar */}
        <nav className="bg-white border border-warm-border rounded-full px-6 py-2 shadow-sm flex items-center gap-6">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`text-sm font-medium transition ${
                  isActive
                    ? 'text-accent-amber font-semibold'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Sync indicators */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 text-text-secondary bg-white border border-warm-border px-3 py-1.5 rounded-full">
            <span className="w-2 h-2 rounded-full bg-risk-stable"></span>
            Health: stable
          </div>
          <div className="text-text-muted">
            V0.1 Local Dev
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-8 pb-12">
        <div className="bg-white border border-warm-border rounded-3xl p-8 min-h-[500px] shadow-sm">
          {children}
        </div>
      </main>
    </div>
  );
}
