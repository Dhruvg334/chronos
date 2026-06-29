import { Link } from 'react-router-dom';
import { ArrowRight, ShieldCheck, Activity, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../components/auth/AuthProvider';

export default function Landing() {
  const { session } = useAuth();

  return (
    <div className="min-h-screen bg-warm-ivory flex flex-col items-center">
      <nav className="w-full max-w-5xl px-6 py-4 flex justify-between items-center">
        <div className="text-xl font-extrabold text-text-primary tracking-tight">ChronOS</div>
        <div className="flex items-center gap-4">
          <Link to="/about" className="text-sm font-semibold text-text-secondary hover:text-text-primary transition-colors">About</Link>
          {session ? (
            <Link to="/command" className="px-4 py-2 text-sm font-semibold text-white bg-accent-amber rounded-lg hover:bg-accent-terracotta transition-colors shadow-sm">
              Go to Command
            </Link>
          ) : (
            <>
              <Link to="/login" className="text-sm font-semibold text-text-secondary hover:text-text-primary transition-colors">Log in</Link>
              <Link to="/signup" className="px-4 py-2 text-sm font-semibold text-white bg-accent-amber rounded-lg hover:bg-accent-terracotta transition-colors shadow-sm">
                Sign up
              </Link>
            </>
          )}
        </div>
      </nav>

      <main className="flex-1 w-full max-w-5xl px-6 py-20 flex flex-col items-center text-center">
        <h1 className="text-5xl md:text-7xl font-extrabold text-text-primary mb-6 tracking-tight max-w-4xl">
          Turn messy commitments into executable <span className="text-accent-amber">recovery paths.</span>
        </h1>
        <p className="text-xl text-text-secondary mb-12 max-w-2xl leading-relaxed">
          A secure AI Time Operating System that predicts deadline collapse before it happens, offering safe, human-approved recovery plans.
        </p>

        {session ? (
          <Link to="/command" className="flex items-center gap-2 px-8 py-4 text-lg font-bold text-white bg-text-primary rounded-xl hover:bg-black transition-colors shadow-sm">
            Open Command Dashboard <ArrowRight className="w-5 h-5" />
          </Link>
        ) : (
          <div className="flex flex-col sm:flex-row gap-4">
            <Link to="/signup" className="flex items-center justify-center gap-2 px-8 py-4 text-lg font-bold text-white bg-accent-amber rounded-xl hover:bg-accent-terracotta transition-colors shadow-sm">
              Get Started for Free <ArrowRight className="w-5 h-5" />
            </Link>
            <Link to="/about" className="flex items-center justify-center gap-2 px-8 py-4 text-lg font-bold text-text-secondary bg-white border border-warm-border rounded-xl hover:bg-warm-cream transition-colors shadow-sm">
              Read the Guide
            </Link>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24 text-left w-full">
          <div className="bg-white p-6 rounded-2xl border border-warm-border shadow-sm">
            <div className="w-12 h-12 bg-warm-cream rounded-xl flex items-center justify-center mb-4">
              <Activity className="w-6 h-6 text-accent-amber" />
            </div>
            <h3 className="text-lg font-bold text-text-primary mb-2">Predict Collapse</h3>
            <p className="text-text-secondary leading-relaxed">ChronOS calculates your real calendar capacity against your remaining effort to warn you when a deadline is slipping.</p>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-warm-border shadow-sm">
            <div className="w-12 h-12 bg-warm-cream rounded-xl flex items-center justify-center mb-4">
              <ShieldCheck className="w-6 h-6 text-risk-stable" />
            </div>
            <h3 className="text-lg font-bold text-text-primary mb-2">Human Approved</h3>
            <p className="text-text-secondary leading-relaxed">The AI generates schedule proposals and rescue interventions, but nothing is executed without your explicit approval.</p>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-warm-border shadow-sm">
            <div className="w-12 h-12 bg-warm-cream rounded-xl flex items-center justify-center mb-4">
              <CheckCircle2 className="w-6 h-6 text-blue-500" />
            </div>
            <h3 className="text-lg font-bold text-text-primary mb-2">Secure by Design</h3>
            <p className="text-text-secondary leading-relaxed">OAuth tokens are secured server-side in Supabase Vault. The frontend never sees your sensitive credentials.</p>
          </div>
        </div>
      </main>

      <footer className="w-full py-8 text-center text-text-muted text-sm border-t border-warm-border">
        &copy; {new Date().getFullYear()} ChronOS. Built for last-minute life savers.
      </footer>
    </div>
  );
}
