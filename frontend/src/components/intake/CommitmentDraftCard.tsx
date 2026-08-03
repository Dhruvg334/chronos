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
      ? 'bg-success-soft text-success'
      : draft.confidence_score > 0.5
        ? 'bg-accent-soft text-accent-strong'
        : 'bg-danger-soft text-danger';

  return (
    <div className="mb-4 rounded-xl border border-line bg-canvas p-5 shadow-sm">
      <div className="mb-3 flex items-start justify-between">
        <div className="flex-1">
          <input
            className="w-full border-b border-transparent bg-transparent text-xl font-semibold text-ink transition-colors hover:border-line focus:border-accent focus:outline-none"
            value={draft.title}
            onChange={(e) => handleChange('title', e.target.value)}
          />
          <div className="mt-2 flex items-center gap-2 text-xs">
            <span className="rounded-md bg-surface-subtle px-2 py-1 font-medium uppercase tracking-wider text-muted">
              {(draft.kind ?? draft.type).replaceAll('_', ' ')}
            </span>
            <span className={`rounded-md px-2 py-1 font-medium ${confidenceClass}`}>
              {Math.round(draft.confidence_score * 100)}% match
            </span>
          </div>
        </div>
        <button
          onClick={onReject}
          className="p-1 text-faint transition-colors hover:text-danger"
          title="Reject commitment"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {(draft.source_text || draft.effort_confidence === 'unknown' || draft.deadline_precision === 'ambiguous') && (
        <div className="mb-4 rounded-lg bg-surface-subtle p-3 text-xs text-muted">
          {draft.source_text && <p>From your wording: “{draft.source_text}”</p>}
          {draft.effort_confidence === 'unknown' && <p className="mt-1">Effort is still uncertain.</p>}
          {draft.deadline_precision === 'ambiguous' && <p className="mt-1">The deadline is a window, not an exact time.</p>}
        </div>
      )}

      {(draft.dependencies?.length ?? 0) > 0 && (
        <div className="mb-4 rounded-lg border border-line bg-accent-soft p-3 text-sm text-accent-strong">
          <strong>Waiting on:</strong> {draft.dependencies!.join(', ')}
        </div>
      )}

      <div className="my-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-xs font-medium text-faint">Estimated minutes</label>
          <input
            type="number"
            min="0"
            className="w-full rounded border border-line bg-surface p-2 text-ink focus:outline-none focus:ring-1 focus:ring-accent"
            value={draft.estimated_minutes || ''}
            placeholder="e.g. 60"
            onChange={(e) => handleChange('estimated_minutes', e.target.value ? parseInt(e.target.value, 10) : null)}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-faint">Deadline</label>
          <input
            type="datetime-local"
            className="w-full rounded border border-line bg-surface p-2 text-ink focus:outline-none focus:ring-1 focus:ring-accent"
            value={draft.deadline_at ? draft.deadline_at.slice(0, 16) : ''}
            onChange={(e) => handleChange('deadline_at', e.target.value ? new Date(e.target.value).toISOString() : null)}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-faint">Importance</label>
          <input
            type="range"
            min="1"
            max="5"
            className="w-full accent-accent"
            value={draft.importance}
            onChange={(e) => handleChange('importance', parseInt(e.target.value, 10))}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-faint">Flexibility</label>
          <input
            type="range"
            min="1"
            max="5"
            className="w-full accent-accent"
            value={draft.flexibility}
            onChange={(e) => handleChange('flexibility', parseInt(e.target.value, 10))}
          />
        </div>
      </div>

      {hasMissing && (
        <div className="mb-4 flex items-start gap-2 rounded-lg border border-line bg-accent-soft p-3 text-sm text-accent-strong">
          <svg className="mt-0.5 h-5 w-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div>
            <strong>Missing context:</strong> Add {draft.missing_fields.join(', ')} to improve planning quality.
          </div>
        </div>
      )}

      {(draft.tasks?.length ?? 0) > 0 && (
        <div className="mt-4 border-t border-line pt-3">
          <label className="mb-2 block text-xs font-medium text-faint">Detected tasks</label>
          <ul className="space-y-1">
            {draft.tasks.map((task, idx) => (
              <li key={idx} className="flex items-center gap-2 text-sm text-muted">
                <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                {task.title} {task.estimated_minutes ? <span className="text-xs text-faint">({task.estimated_minutes}m)</span> : ''}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
