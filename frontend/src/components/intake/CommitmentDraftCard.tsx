import React from 'react';
import type { CommitmentDraft } from '../../types/api';

type DraftFieldValue = string | number | null;

interface CommitmentDraftCardProps {
  draft: CommitmentDraft;
  onUpdate: (updatedDraft: CommitmentDraft) => void;
  onReject: () => void;
}

export const CommitmentDraftCard: React.FC<CommitmentDraftCardProps> = ({ draft, onUpdate, onReject }) => {
  const handleChange = (field: keyof CommitmentDraft, value: DraftFieldValue) => {
    onUpdate({ ...draft, [field]: value });
  };

  const hasMissing = draft.missing_fields && draft.missing_fields.length > 0;

  const confidenceClass =
    draft.confidence_score > 0.8
      ? 'bg-green-50 text-risk-stable'
      : draft.confidence_score > 0.5
        ? 'bg-warm-cream text-risk-watch'
        : 'bg-red-50 text-risk-atrisk';

  return (
    <div className="mb-4 rounded-xl border border-warm-border bg-warm-ivory p-5 shadow-sm">
      <div className="mb-3 flex items-start justify-between">
        <div className="flex-1">
          <input
            className="w-full border-b border-transparent bg-transparent text-xl font-semibold text-text-primary transition-colors hover:border-warm-border focus:border-accent-amber focus:outline-none"
            value={draft.title}
            onChange={(e) => handleChange('title', e.target.value)}
          />
          <div className="mt-2 flex items-center gap-2 text-xs">
            <span className="rounded-md bg-warm-surface px-2 py-1 font-medium uppercase tracking-wider text-text-secondary">
              {draft.type}
            </span>
            <span className={`rounded-md px-2 py-1 font-medium ${confidenceClass}`}>
              {Math.round(draft.confidence_score * 100)}% match
            </span>
          </div>
        </div>
        <button
          onClick={onReject}
          className="p-1 text-text-muted transition-colors hover:text-risk-atrisk"
          title="Reject commitment"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="my-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-xs font-medium text-text-muted">Estimated minutes</label>
          <input
            type="number"
            min="0"
            className="w-full rounded border border-warm-border bg-white p-2 text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-amber"
            value={draft.estimated_minutes || ''}
            placeholder="e.g. 60"
            onChange={(e) => handleChange('estimated_minutes', e.target.value ? parseInt(e.target.value, 10) : null)}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-text-muted">Deadline</label>
          <input
            type="datetime-local"
            className="w-full rounded border border-warm-border bg-white p-2 text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-amber"
            value={draft.deadline_at ? draft.deadline_at.slice(0, 16) : ''}
            onChange={(e) => handleChange('deadline_at', e.target.value ? new Date(e.target.value).toISOString() : null)}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-text-muted">Importance</label>
          <input
            type="range"
            min="1"
            max="5"
            className="w-full accent-accent-amber"
            value={draft.importance}
            onChange={(e) => handleChange('importance', parseInt(e.target.value, 10))}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-text-muted">Flexibility</label>
          <input
            type="range"
            min="1"
            max="5"
            className="w-full accent-accent-amber"
            value={draft.flexibility}
            onChange={(e) => handleChange('flexibility', parseInt(e.target.value, 10))}
          />
        </div>
      </div>

      {hasMissing && (
        <div className="mb-4 flex items-start gap-2 rounded-lg border border-warm-border bg-warm-cream p-3 text-sm text-risk-watch">
          <svg className="mt-0.5 h-5 w-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div>
            <strong>Missing context:</strong> Add {draft.missing_fields.join(', ')} to improve planning quality.
          </div>
        </div>
      )}

      {(draft.tasks?.length ?? 0) > 0 && (
        <div className="mt-4 border-t border-warm-border pt-3">
          <label className="mb-2 block text-xs font-medium text-text-muted">Detected tasks</label>
          <ul className="space-y-1">
            {draft.tasks.map((task, idx) => (
              <li key={idx} className="flex items-center gap-2 text-sm text-text-secondary">
                <span className="h-1.5 w-1.5 rounded-full bg-accent-amber" />
                {task.title} {task.estimated_minutes ? <span className="text-xs text-text-muted">({task.estimated_minutes}m)</span> : ''}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
