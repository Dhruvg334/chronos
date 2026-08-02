import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldAlert, Loader2, Mail } from 'lucide-react';
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
    if (pass.length < 8) return "Password must be at least 8 characters.";
    if (pass.toLowerCase() === 'password') return "Password cannot be 'password'.";
    if (pass === '12345678') return "Password is too common.";
    if (pass === 'qwerty') return "Password is too common.";
    
    const localPart = emailStr.split('@')[0];
    if (localPart && pass.toLowerCase().includes(localPart.toLowerCase())) {
      return "Password cannot contain your email username.";
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Basic Validation
    if (!email || !password || !confirmPassword) {
      setError('All fields are required.');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    const passError = validatePassword(password, email);
    if (passError) {
      setError(passError);
      return;
    }
    if (!isSupabaseConfigured) {
      setError('Authentication is not configured in this environment.');
      return;
    }

    setIsLoading(true);
    try {
      const { error: signUpError } = await supabase.auth.signUp({
        email,
        password,
      });

      if (signUpError) {
        throw signUpError;
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
      <div className="flex h-screen items-center justify-center bg-canvas p-4">
        <div className="w-full max-w-md bg-surface border border-line rounded-2xl shadow-sm p-8 text-center">
          <div className="w-16 h-16 bg-accent-soft border border-line rounded-full flex items-center justify-center mx-auto mb-6">
            <Mail className="w-8 h-8 text-accent-strong" />
          </div>
          <h2 className="text-2xl font-bold text-ink mb-3">Check your email</h2>
          <p className="text-muted mb-6">
            We've sent a verification link to <strong>{email}</strong>. Please verify your account before logging in.
          </p>
          <button
            onClick={() => navigate('/login')}
            className="w-full bg-surface border border-line text-ink py-2.5 rounded-lg font-semibold hover:bg-canvas transition-colors"
          >
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen items-center justify-center bg-canvas p-4">
      <div className="w-full max-w-md bg-surface border border-line rounded-2xl shadow-sm p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-extrabold text-ink mb-2">Create an account</h1>
          <p className="text-muted">Build a realistic plan around your commitments and available time.</p>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-danger-soft border border-danger text-danger text-sm rounded-lg flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-muted mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 bg-surface border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent text-ink"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-muted mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 bg-surface border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent text-ink"
              placeholder="At least 8 characters"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-muted mb-1">Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-2 bg-surface border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent text-ink"
              placeholder="Repeat your password"
            />
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 bg-accent text-white py-2.5 rounded-lg font-semibold hover:bg-accent-strong transition-colors disabled:opacity-50"
          >
            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            Sign Up
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-muted">
          Already have an account?{' '}
          <Link to="/login" className="text-accent-strong font-semibold hover:underline">
            Log in
          </Link>
        </div>
      </div>
    </div>
  );
}
