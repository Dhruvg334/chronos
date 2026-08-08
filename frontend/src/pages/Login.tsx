import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2, Loader2, ShieldAlert } from 'lucide-react';
import { isSupabaseConfigured, supabase } from '../lib/supabase';
import { useAuth } from '../components/auth/auth-context';

export default function Login() {
  const navigate = useNavigate();
  const { session } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  useEffect(() => { if (session) navigate('/today'); }, [session, navigate]);
  if (session) return null;

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email || !password) return setError('Please enter both email and password.');
    if (!isSupabaseConfigured) return setError('Authentication is not configured in this environment.');
    setIsLoading(true);
    try {
      const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
      if (signInError) throw signInError;
      navigate('/today');
    } catch {
      setError('Invalid credentials or email not verified.');
    } finally { setIsLoading(false); }
  };

  const handleGoogleLogin = async () => {
    setError(null);
    setIsGoogleLoading(true);
    if (!isSupabaseConfigured) { setError('Authentication is not configured in this environment.'); setIsGoogleLoading(false); return; }
    try {
      const { data, error: googleError } = await supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: `${window.location.origin}/today` } });
      if (googleError) throw googleError;
      if (!data?.url) throw new Error('Google login provider is not configured correctly in Supabase.');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to initialize Google Login.';
      setError(message.includes('provider is not supported') ? 'Google login is not currently configured in this environment.' : message);
      setIsGoogleLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <aside className="auth-story">
          <Link to="/" className="brand-wordmark">Chron<span className="brand-os">OS</span></Link>
          <div className="max-w-sm">
            <p className="eyebrow">Return to your day</p>
            <h2 className="mt-4 text-4xl font-semibold leading-[1.05] tracking-[-0.04em]">Know what fits. Do what matters. Repair the rest.</h2>
            <ul className="mt-7 space-y-4 text-sm leading-6 text-muted">
              <li className="flex gap-3"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-accent" />One clear next action instead of another dashboard.</li>
              <li className="flex gap-3"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-accent" />Plans constrained by capacity, buffers, and dependencies.</li>
              <li className="flex gap-3"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-accent" />Recommendations explain trade-offs before anything changes.</li>
            </ul>
          </div>
          <p className="text-xs text-faint">Your plan, with your approval boundary</p>
        </aside>

        <main className="auth-form-wrap">
          <div className="auth-form motion-enter">
            <div className="lg:hidden"><Link to="/" className="brand-wordmark">Chron<span className="brand-os">OS</span></Link></div>
            <p className="eyebrow mt-9 lg:mt-0">ChronOS</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">Welcome back</h1>
            <p className="mt-2 text-sm leading-6 text-muted">Log in to pick up your plan where you left it.</p>

            {error && <div role="alert" className="mt-5 flex items-start gap-2 rounded-xl border border-danger/20 bg-danger-soft p-3 text-sm text-danger"><ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" /><span>{error}</span></div>}

            <button onClick={handleGoogleLogin} disabled={isGoogleLoading || isLoading} className="button-secondary mt-7 w-full gap-3">
              {isGoogleLoading ? <Loader2 className="h-5 w-5 animate-spin text-faint" /> : <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>}
              Continue with Google
            </button>

            <div className="my-6 flex items-center gap-3"><span className="h-px flex-1 bg-line"/><span className="text-xs font-medium text-faint">or use email</span><span className="h-px flex-1 bg-line"/></div>

            <form onSubmit={handleEmailLogin} className="space-y-4">
              <label className="label">Email<input aria-label="Email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className="field mt-1" placeholder="you@example.com" /></label>
              <label className="label">Password<input aria-label="Password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} className="field mt-1" placeholder="••••••••" /></label>
              <button type="submit" disabled={isLoading || isGoogleLoading} className="button-primary mt-2 w-full">{isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Log in<ArrowRight className="ml-2 h-4 w-4" /></button>
            </form>

            <p className="mt-6 text-center text-sm text-muted">Don't have an account? <Link to="/signup" className="font-semibold text-ink hover:underline">Sign up</Link></p>
          </div>
        </main>
      </div>
    </div>
  );
}
