import AppShell from '../components/layout/AppShell';

export default function Calendar() {
  return (
    <AppShell>
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-3xl font-extrabold">Calendar Capacity</h2>
            <p className="text-text-secondary">Sync your calendar to schedule focus blocks.</p>
          </div>
          <button disabled className="px-4 py-2 bg-warm-surface border border-warm-border text-text-muted rounded-lg text-sm font-semibold">
            Connect Google Calendar
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Calendar grid view mockup */}
          <div className="md:col-span-3 bg-warm-cream border border-warm-border rounded-2xl p-6 h-96 flex items-center justify-center text-text-muted text-sm">
            [Google Calendar Sync Grid — Phase 0]
          </div>

          {/* Allocation details column */}
          <div className="md:col-span-1 bg-warm-cream border border-warm-border rounded-2xl p-6 flex flex-col justify-between">
            <div>
              <h3 className="font-bold text-sm mb-4">Focus Allocation</h3>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between">
                  <span>Deep Work</span>
                  <span className="font-semibold">0 hrs</span>
                </div>
                <div className="flex justify-between">
                  <span>Shallow Work</span>
                  <span className="font-semibold">0 hrs</span>
                </div>
                <div className="flex justify-between">
                  <span>Buffer Zones</span>
                  <span className="font-semibold">0 hrs</span>
                </div>
              </div>
            </div>
            <div className="text-xs text-text-muted mt-8 border-t border-warm-border pt-4">
              Connect accounts to load allocation charts.
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
