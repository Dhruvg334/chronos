import { useState } from 'react';

export interface SkipPayload {
  reason: string;
  notes?: string;
}

interface SkipModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: SkipPayload) => Promise<void>;
  blockId: string;
}

export default function SkipModal({ isOpen, onClose, onSubmit }: SkipModalProps) {
  const [reason, setReason] = useState('blocked');
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
        reason,
        notes: notes || undefined,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ChronOS could not skip this focus block.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-text-primary/40 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md overflow-hidden rounded-xl border border-warm-border bg-warm-ivory shadow-xl">
        <div className="border-b border-warm-border px-6 py-4">
          <h2 className="text-xl font-bold text-text-primary">Skip focus block</h2>
          <p className="text-sm text-text-muted">Skipping updates risk so the plan stays honest.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-6">
          {error && (
            <div className="rounded-lg border border-risk-atrisk bg-red-50 p-3 text-sm text-risk-atrisk">
              {error}
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">Reason</label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full rounded-md border border-warm-border bg-white px-3 py-2 text-text-primary focus:border-accent-amber focus:outline-none focus:ring-2 focus:ring-accent-amber/30"
            >
              <option value="blocked">Blocked</option>
              <option value="interrupted">Interrupted</option>
              <option value="low_energy">Low energy</option>
              <option value="postponed">Postponed</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">Details</label>
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
              className="rounded-lg bg-risk-atrisk px-4 py-2 font-medium text-white shadow-sm transition-colors hover:bg-risk-critical disabled:opacity-50"
            >
              {submitting ? 'Skipping…' : 'Skip block'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
