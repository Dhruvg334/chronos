import AppShell from '../components/layout/AppShell';

export default function Reflection() {
  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl font-extrabold mb-2">Reflection & Calibration</h2>
        <p className="text-text-secondary mb-6">
          Review your performance logs to calibrate estimate-vs-actual coefficients in memory.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Overrun metrics */}
          <div className="bg-warm-cream border border-warm-border rounded-xl p-6 text-center">
            <span className="text-2xl font-bold block text-accent-terracotta">1.0x</span>
            <span className="text-xs text-text-secondary font-semibold">Overrun Factor</span>
          </div>

          <div className="bg-warm-cream border border-warm-border rounded-xl p-6 text-center">
            <span className="text-2xl font-bold block text-risk-stable">0%</span>
            <span className="text-xs text-text-secondary font-semibold">Estimation Error</span>
          </div>

          <div className="bg-warm-cream border border-warm-border rounded-xl p-6 text-center">
            <span className="text-2xl font-bold block text-text-primary">0</span>
            <span className="text-xs text-text-secondary font-semibold">Blocks Reviewed</span>
          </div>
        </div>

        {/* reflection history placeholder */}
        <div className="border border-dashed border-warm-border rounded-2xl p-8 mt-8 text-center text-text-muted text-sm h-48 flex items-center justify-center">
          [Reflection Questionnaire logs — Phase 0]
        </div>
      </div>
    </AppShell>
  );
}
