import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2, Loader2, Mail, ShieldAlert } from 'lucide-react';
import { isSupabaseConfigured, supabase } from '../lib/supabase';

export default function Signup() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const validatePassword = (pass: string, emailStr: string) => {
    if (pass.length < 8) return 'Password must be at least 8 characters.';
    if (pass.toLowerCase() === 'password') return "Password cannot be 'password'.";
    if (pass === '12345678' || pass === 'qwerty') return 'Password is too common.';
    const localPart = emailStr.split('@')[0];
    if (localPart && pass.toLowerCase().includes(localPart.toLowerCase())) return 'Password cannot contain your email username.';
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !password || !confirmPassword) return setError('All fields are required.');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return setError('Please enter a valid email address.');
    if (password !== confirmPassword) return setError('Passwords do not match.');
    const passError = validatePassword(password, email);
    if (passError) return setError(passError);
    if (!isSupabaseConfigured) return setError('Authentication is not configured in this environment.');

    setIsLoading(true);
    try {
      const { data, error: signUpError } = await supabase.auth.signUp({ email, password });
      if (signUpError) throw signUpError;

      // Local Supabase commonly runs with email confirmation disabled. In that mode
      // signUp returns a valid session immediately, so the truthful next step is setup.
      if (data.session) {
        navigate('/onboarding', { replace: true });
        return;
      }
      setIsSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create your account.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="auth-shell">
        <div className="auth-panel lg:grid-cols-1">
          <div className="auth-form-wrap">
            <div className="auth-form text-center motion-pop">
              <Link to="/" className="brand-wordmark mb-10">Chron<span className="brand-os">OS</span></Link>
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-accent-soft text-accent-strong"><Mail className="h-5 w-5" /></div>
              <h1 className="mt-5 text-2xl font-semibold tracking-[-0.03em]">Check your email</h1>
              <p className="mt-2 text-sm leading-6 text-muted">We sent a verification link to <strong className="font-semibold text-ink">{email}</strong>. Open it once, then continue to ChronOS.</p>
              <button onClick={() => navigate('/login')} className="button-primary mt-7 w-full">Return to Login</button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <aside className="auth-story">
          <Link to="/" className="brand-wordmark">Chron<span className="brand-os">OS</span></Link>
          <div className="max-w-sm">
            <p className="eyebrow">Start with reality</p>
            <h2 className="mt-4 text-4xl font-semibold leading-[1.05] tracking-[-0.04em]">A plan should fit your life before it asks you to follow it.</h2>
            <ul className="mt-7 space-y-4 text-sm leading-6 text-muted">
              <li className="flex gap-3"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-accent" />Capacity and calendar constraints stay visible.</li>
              <li className="flex gap-3"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-accent" />Important changes wait for your approval.</li>
              <li className="flex gap-3"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-accent" />Recovery is part of the plan, not a failure state.</li>
            </ul>
          </div>
          <p className="text-xs text-faint">Private by default · explicit control</p>
        </aside>

        <main className="auth-form-wrap">
          <div className="auth-form motion-enter">
            <div className="lg:hidden"><Link to="/" className="brand-wordmark">Chron<span className="brand-os">OS</span></Link></div>
            <p className="eyebrow mt-9 lg:mt-0">Create your workspace</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">Create an account</h1>
            <p className="mt-2 text-sm leading-6 text-muted">Set up a realistic planning system around the time you actually have.</p>

            {error && <div role="alert" className="mt-5 flex items-start gap-2 rounded-xl border border-danger/20 bg-danger-soft p-3 text-sm text-danger"><ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" /><span>{error}</span></div>}

            <form onSubmit={handleSubmit} noValidate className="mt-7 space-y-4">
              <label className="label">Email<input aria-label="Email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className="field mt-1" placeholder="you@example.com" /></label>
              <label className="label">Password<input aria-label="Password" type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} className="field mt-1" placeholder="At least 8 characters" /></label>
              <label className="label">Confirm Password<input aria-label="Confirm Password" type="password" autoComplete="new-password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="field mt-1" placeholder="Repeat your password" /></label>
              <button type="submit" disabled={isLoading} className="button-primary mt-2 w-full">
                {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}Sign Up<ArrowRight className="ml-2 h-4 w-4" />
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-muted">Already have an account? <Link to="/login" className="font-semibold text-ink hover:underline">Log in</Link></p>
          </div>
        </main>
      </div>
    </div>
  );
}
