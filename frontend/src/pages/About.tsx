import { ShieldCheck, CalendarCheck, CheckCircle2, Activity, BrainCircuit } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function About() {
  return (
    <div className="min-h-screen bg-warm-ivory text-text-primary">
      <nav className="w-full max-w-4xl mx-auto px-6 py-4 flex justify-between items-center border-b border-warm-border">
        <Link to="/" className="text-xl font-extrabold tracking-tight">ChronOS</Link>
        <div className="flex items-center gap-4">
          <Link to="/command" className="text-sm font-semibold text-text-secondary hover:text-text-primary transition-colors">Command</Link>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-6 py-12 space-y-12">
        <header className="mb-12">
          <h1 className="text-4xl font-extrabold tracking-tight mb-4">About ChronOS</h1>
          <p className="text-lg text-text-secondary leading-relaxed">
            Turn messy commitments into executable recovery paths with human-approved AI planning.
          </p>
        </header>

        <section className="bg-white p-8 rounded-2xl border border-warm-border shadow-sm">
          <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
            <Activity className="w-6 h-6 text-accent-amber" />
            Mission & Problem
          </h2>
          <p className="text-text-secondary leading-relaxed mb-4">
            ChronOS helps overwhelmed users regain control when commitments, deadlines, limited energy, and strict calendar realities conflict. Traditional task managers wait for you to fail, and autonomous agents make risky decisions without context. 
          </p>
          <p className="text-text-secondary leading-relaxed">
            ChronOS acts as a "last-minute life saver"—predicting deadline collapse before it happens and offering safe, executable recovery paths.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <BrainCircuit className="w-6 h-6 text-text-muted" />
            What ChronOS Does
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { title: 'Brain Dump Intake', desc: 'Converts unstructured thoughts into tracked commitments.' },
              { title: 'Risk Engine', desc: 'Predicts failure by comparing remaining effort against available calendar time.' },
              { title: 'Schedule Proposals', desc: 'Generates optimized focus blocks to fit your actual capacity.' },
              { title: 'Rescue Actions', desc: 'Proposes scope reduction or urgent recovery paths for failing commitments.' }
            ].map(f => (
              <div key={f.title} className="bg-warm-cream p-4 rounded-xl border border-warm-border">
                <h3 className="font-bold text-sm mb-1">{f.title}</h3>
                <p className="text-xs text-text-secondary">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="bg-white p-8 rounded-2xl border border-warm-border shadow-sm">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <CheckCircle2 className="w-6 h-6 text-risk-stable" />
            How to use ChronOS
          </h2>
          <ol className="list-decimal list-inside space-y-3 text-text-secondary">
            <li><strong>Brain dump</strong> commitments into the Inbox.</li>
            <li><strong>Review</strong> and adjust extracted deadlines and effort estimates.</li>
            <li><strong>Run ChronOS Analysis</strong> from Command.</li>
            <li><strong>Review suggested actions</strong> (focus blocks or rescue interventions) in the Decision Dock.</li>
            <li><strong>Approve</strong> only the actions that make sense for your reality.</li>
            <li><strong>Reflect and adjust</strong> after work sessions to improve future risk modeling.</li>
          </ol>
        </section>

        <section className="bg-red-50 p-8 rounded-2xl border border-risk-atrisk shadow-sm">
          <h2 className="text-2xl font-bold mb-4 flex items-center gap-2 text-risk-atrisk">
            <ShieldCheck className="w-6 h-6 text-risk-atrisk" />
            Safety & Human Approval
          </h2>
          <ul className="list-disc list-inside space-y-2 text-risk-critical text-sm font-medium">
            <li>ChronOS proposes; you approve.</li>
            <li>No focus blocks are created without your explicit approval.</li>
            <li>ChronOS does not write to your Google Calendar.</li>
            <li>No external emails or messages are sent automatically.</li>
            <li>OAuth tokens are secured server-side via Supabase Vault; the frontend never receives sensitive credentials.</li>
          </ul>
        </section>

        <section className="bg-white p-8 rounded-2xl border border-warm-border shadow-sm">
          <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
            <CalendarCheck className="w-6 h-6 text-green-600" />
            Google Integration
          </h2>
          <p className="text-text-secondary leading-relaxed text-sm">
            ChronOS uses the Gemini API for structured intent extraction and plan explanation. 
            It requests read-only access to your Google Calendar to accurately calculate your free focus time. 
            Authentication is handled securely via Supabase Auth's Google OAuth provider.
          </p>
        </section>

        <footer className="pt-8 border-t border-warm-border text-center text-sm text-text-muted">
          <p>ChronOS — Built as a real product foundation for deadline recovery.</p>
          <div className="mt-4 space-x-4">
            <Link to="/login" className="hover:text-text-primary transition-colors">Log In</Link>
            <Link to="/signup" className="hover:text-text-primary transition-colors">Sign Up</Link>
          </div>
        </footer>
      </main>
    </div>
  );
}
