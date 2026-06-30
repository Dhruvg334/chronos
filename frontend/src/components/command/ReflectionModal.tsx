import { useState } from 'react';

export interface ReflectionPayload {
  actual_minutes: number;
  energy_level: number;
  completion_status: string;
  progress_percent_update?: number;
  notes?: string;
}

interface ReflectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ReflectionPayload) => Promise<void>;
  blockId: string;
}

export default function ReflectionModal({ isOpen, onClose, onSubmit }: ReflectionModalProps) {
  const [actualMinutes, setActualMinutes] = useState(30);
  const [energyLevel, setEnergyLevel] = useState(3);
  const [completionStatus] = useState('completed');
  const [progressUpdate, setProgressUpdate] = useState(0);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({
        actual_minutes: actualMinutes,
        energy_level: energyLevel,
        completion_status: completionStatus,
        progress_percent_update: progressUpdate > 0 ? progressUpdate : undefined,
        notes: notes || undefined,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ChronOS could not save this reflection.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-text-primary/40 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md overflow-hidden rounded-xl border border-warm-border bg-warm-ivory shadow-xl">
        <div className="border-b border-warm-border px-6 py-4">
          <h2 className="text-xl font-bold text-text-primary">Focus block complete</h2>
          <p className="text-sm text-text-muted">Reflect on your time so ChronOS can adjust the plan.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-6">
          {error && (
            <div className="rounded-lg border border-risk-atrisk bg-red-50 p-3 text-sm text-risk-atrisk">
              {error}
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">Time spent in minutes</label>
            <input
              type="number"
              min="0"
              value={actualMinutes}
              onChange={(e) => setActualMinutes(Number(e.target.value))}
              className="w-full rounded-md border border-warm-border bg-white px-3 py-2 text-text-primary focus:border-accent-amber focus:outline-none focus:ring-2 focus:ring-accent-amber/30"
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">Energy level</label>
            <input
              type="range"
              min="1"
              max="5"
              value={energyLevel}
              onChange={(e) => setEnergyLevel(Number(e.target.value))}
              className="w-full accent-accent-amber"
            />
            <div className="mt-1 flex justify-between text-xs text-text-muted">
              <span>Drained</span>
              <span>Energized</span>
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">New total progress %</label>
            <input
              type="number"
              min="0"
              max="100"
              placeholder="e.g. 50"
              value={progressUpdate || ''}
              onChange={(e) => setProgressUpdate(Number(e.target.value))}
              className="w-full rounded-md border border-warm-border bg-white px-3 py-2 text-text-primary focus:border-accent-amber focus:outline-none focus:ring-2 focus:ring-accent-amber/30"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">Notes</label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full rounded-md border border-warm-border bg-white px-3 py-2 text-text-primary focus:border-accent-amber focus:outline-none focus:ring-2 focus:ring-accent-amber/30"
            />
          </div>

          <div className="mt-6 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="rounded-lg px-4 py-2 font-medium text-text-secondary transition-colors hover:bg-warm-surface disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-accent-amber px-4 py-2 font-medium text-white shadow-sm transition-colors hover:bg-accent-terracotta disabled:opacity-50"
            >
              {submitting ? 'Saving…' : 'Complete block'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
