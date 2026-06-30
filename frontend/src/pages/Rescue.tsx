import AppShell from '../components/layout/AppShell';

export default function Rescue() {
  return (
    <AppShell>
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-extrabold text-risk-critical mb-2">Rescue Console</h2>
        <p className="text-text-secondary mb-6">
          Minimum Viable Completion Paths (MVCP) for near-failing commitments.
        </p>

        <div className="bg-risk-rescue/5 border border-risk-rescue/20 rounded-2xl p-8 text-center flex flex-col items-center justify-center min-h-[300px]">
          <span className="w-12 h-12 rounded-full bg-risk-rescue/10 text-risk-rescue flex items-center justify-center font-bold text-xl mb-4">
            🛡️
          </span>
          <h3 className="text-lg font-bold text-risk-rescue mb-1">No Active Critical Commitments</h3>
          <p className="text-xs text-text-secondary max-w-sm">
            Rescue mode triggers automatically when commitment risk reaches Critical levels or when manually activated.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
