import AppShell from '../components/layout/AppShell';

export default function Command() {
  return (
    <AppShell>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
        {/* Left Column: Time Spine Panel placeholder */}
        <div className="lg:col-span-1 bg-warm-cream border border-warm-border rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold mb-2">Time Spine</h3>
            <p className="text-sm text-text-secondary">Your commitments mapped as a chronological axis.</p>
          </div>
          <div className="border border-dashed border-warm-border rounded-xl h-64 flex items-center justify-center text-text-muted text-xs">
            [TimeSpine Visual Placeholder — Phase 0]
          </div>
        </div>

        {/* Center Column: Active Focus Console placeholder */}
        <div className="lg:col-span-1 bg-warm-cream border border-warm-border rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold mb-2 text-accent-terracotta">Active Focus Console</h3>
            <p className="text-sm text-text-secondary">Your current action contract is displayed here.</p>
          </div>
          <div className="bg-white border border-warm-border rounded-xl p-4 my-4 flex-1 flex flex-col items-center justify-center text-center">
            <h4 className="font-semibold text-base mb-1">Study for Exam</h4>
            <span className="text-xs text-text-muted mb-4">Done condition: Finish 2 modules</span>
            <div className="text-3xl font-mono font-bold mb-4 text-text-primary">45:00</div>
            <button disabled className="px-4 py-2 bg-warm-surface border border-warm-border rounded-full text-xs text-text-muted font-medium">
              Start Block
            </button>
          </div>
        </div>

        {/* Right Column: Agent Console placeholder */}
        <div className="lg:col-span-1 bg-warm-cream border border-warm-border rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold mb-2 text-accent-amber">Agent Console</h3>
            <p className="text-sm text-text-secondary">Explainable reasoning logs from background runners.</p>
          </div>
          <div className="bg-text-primary text-warm-ivory font-mono text-xs rounded-xl p-4 h-64 overflow-y-auto space-y-2 mt-4">
            <p className="text-text-muted">[21:42:01] Initializing Agent Console...</p>
            <p className="text-accent-amber">[21:42:02] Trace stream active (Mocked)</p>
            <p className="text-accent-amber">[21:42:03] Standby: Ready for commitments</p>
          </div>
        </div>

        {/* Bottom row: Drift Radar & Decision Dock */}
        <div className="lg:col-span-3 bg-warm-cream border border-warm-border rounded-2xl p-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-lg font-bold">Drift Radar & Decision Dock</h3>
              <p className="text-sm text-text-secondary">Compare plan vs. actual performance deviations.</p>
            </div>
            <span className="px-3 py-1 bg-risk-stable text-white text-xs font-semibold rounded-full">
              Stable
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white border border-warm-border rounded-xl p-4 flex items-center justify-center text-xs text-text-muted h-24">
              [Drift Logs List — Phase 0]
            </div>
            <div className="bg-white border border-warm-border rounded-xl p-4 flex items-center justify-center text-xs text-text-muted h-24">
              [Pending Approvals Queue — Phase 0]
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
