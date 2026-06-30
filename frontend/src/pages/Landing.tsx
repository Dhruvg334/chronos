import { Link } from 'react-router-dom';
import { useAuth } from '../components/auth/AuthProvider';

export default function Landing() {
  const { session } = useAuth();

  return (
    <div className="min-h-screen bg-warm-ivory flex flex-col items-center justify-center p-6">
      <main className="w-full max-w-2xl bg-white border border-warm-border rounded-3xl p-10 md:p-14 shadow-sm text-center">
        <h1 className="text-4xl md:text-5xl font-extrabold text-text-primary mb-4 tracking-tight">
          Chron<span className="text-accent-amber">OS</span>
        </h1>
        
        <p className="text-xl text-text-secondary mb-8 leading-relaxed">
          A calm AI time operating system for turning messy commitments into recovery plans.
        </p>

        <ul className="text-left max-w-md mx-auto space-y-4 mb-10 text-text-secondary text-sm md:text-base">
          <li className="flex items-start gap-3">
            <span className="text-accent-amber font-bold mt-0.5">•</span>
            <span>Brain dump your commitments into a single structured queue.</span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-accent-amber font-bold mt-0.5">•</span>
            <span>Run agent analysis against your real calendar capacity.</span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-accent-amber font-bold mt-0.5">•</span>
            <span>Approve only the focus blocks and rescue actions you want.</span>
          </li>
        </ul>

        {session ? (
          <Link to="/command" className="inline-block px-8 py-3 text-base font-bold text-white bg-accent-amber rounded-xl hover:bg-accent-terracotta transition-colors shadow-sm w-full sm:w-auto">
            Open Command
          </Link>
        ) : (
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link to="/demo" className="w-full sm:w-auto px-8 py-3 text-base font-bold text-white bg-accent-amber rounded-xl hover:bg-accent-terracotta transition-colors shadow-sm text-center">
              Try demo
            </Link>
            <Link to="/signup" className="w-full sm:w-auto px-8 py-3 text-base font-bold text-text-primary bg-white border border-warm-border rounded-xl hover:bg-warm-ivory transition-colors shadow-sm text-center">
              Sign up
            </Link>
            <Link to="/login" className="w-full sm:w-auto px-8 py-3 text-base font-bold text-text-secondary bg-warm-ivory border border-warm-border rounded-xl hover:bg-warm-border transition-colors shadow-sm text-center">
              Log in
            </Link>
          </div>
        )}

        <div className="mt-10 pt-6 border-t border-warm-border text-sm">
          <Link to="/about" className="text-text-muted hover:text-text-primary font-semibold transition-colors">
            Read the guide →
          </Link>
        </div>
      </main>
    </div>
  );
}
