import AppShell from '../components/layout/AppShell';

export default function Inbox() {
  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl font-extrabold mb-2">Brain Dump Intake</h2>
        <p className="text-text-secondary mb-6">
          Dump your messy scheduling plans and let ChronOS parse them into structured commitments.
        </p>

        <div className="space-y-6">
          {/* Intake Textarea input */}
          <div className="bg-warm-cream border border-warm-border rounded-2xl p-6">
            <label className="block text-sm font-semibold mb-2">Messy Week Brain Dump</label>
            <textarea
              disabled
              placeholder="Example: Need to finish my database schema by Tuesday and review slides. Also study for exam on Friday at 9am. (Intake disabled for Phase 0)"
              rows={6}
              className="w-full p-4 border border-warm-border rounded-xl bg-white resize-none text-sm text-text-muted"
            />
            <div className="mt-4 flex justify-between items-center">
              <span className="text-xs text-text-muted">Requires Gemini integration</span>
              <button disabled className="px-6 py-2.5 bg-warm-surface border border-warm-border text-text-muted font-semibold rounded-lg text-sm">
                Compile Commitments
              </button>
            </div>
          </div>

          {/* Extracted Review container */}
          <div className="border border-dashed border-warm-border rounded-2xl p-8 flex flex-col items-center justify-center text-center text-text-muted text-sm h-48">
            [Extracted Commitments Review Panel — Phase 0]
          </div>
        </div>
      </div>
    </AppShell>
  );
}
