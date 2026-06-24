import AppShell from '../components/layout/AppShell';

export default function Settings() {
  return (
    <AppShell>
      <div className="max-w-3xl mx-auto">
        <h2 className="text-3xl font-extrabold mb-2">System Settings</h2>
        <p className="text-text-secondary mb-6">Manage planning, integration, and agent preferences.</p>

        <div className="space-y-6">
          {/* Autonomy Level Settings card */}
          <div className="bg-warm-cream border border-warm-border rounded-xl p-6">
            <h3 className="font-bold text-base mb-2">Autonomy Level</h3>
            <p className="text-xs text-text-secondary mb-4">Define backend agent execution boundaries.</p>
            <div className="flex flex-wrap gap-3">
              {['Suggest', 'Ask', 'Act low-risk', 'Rescue intervention', 'External write'].map((level, i) => (
                <button
                  key={level}
                  disabled
                  className={`px-4 py-2 text-xs font-semibold rounded-full border ${
                    i === 1
                      ? 'bg-accent-amber border-accent-amber text-white'
                      : 'bg-white border-warm-border text-text-secondary'
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>

          {/* Timezone and working hours card */}
          <div className="bg-warm-cream border border-warm-border rounded-xl p-6 space-y-4">
            <h3 className="font-bold text-base">Planning Constraints</h3>
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block text-text-secondary font-semibold mb-1">Timezone</label>
                <input
                  type="text"
                  disabled
                  placeholder="UTC"
                  className="w-full p-2 border border-warm-border rounded-lg bg-white text-text-muted"
                />
              </div>
              <div>
                <label className="block text-text-secondary font-semibold mb-1">Working Hours</label>
                <input
                  type="text"
                  disabled
                  placeholder="09:00 - 17:00"
                  className="w-full p-2 border border-warm-border rounded-lg bg-white text-text-muted"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
