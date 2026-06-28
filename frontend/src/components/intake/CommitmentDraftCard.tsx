import React from 'react';
import { CommitmentDraft } from '../../types/api';

interface CommitmentDraftCardProps {
  draft: CommitmentDraft;
  onUpdate: (updatedDraft: CommitmentDraft) => void;
  onReject: () => void;
}

export const CommitmentDraftCard: React.FC<CommitmentDraftCardProps> = ({ draft, onUpdate, onReject }) => {
  const handleChange = (field: keyof CommitmentDraft, value: any) => {
    onUpdate({ ...draft, [field]: value });
  };

  const hasMissing = draft.missing_fields && draft.missing_fields.length > 0;

  return (
    <div className="bg-[#FAF9F6] border border-[#E5E0D8] rounded-xl p-5 shadow-sm mb-4">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <input
            className="text-xl font-semibold text-[#2C2B29] bg-transparent border-b border-transparent hover:border-[#D1CCC2] focus:border-[#B57C45] focus:outline-none w-full transition-colors"
            value={draft.title}
            onChange={(e) => handleChange('title', e.target.value)}
          />
          <div className="flex gap-2 mt-2 items-center text-xs">
            <span className="px-2 py-1 bg-[#F0EBE1] text-[#5C5A56] rounded-md font-medium uppercase tracking-wider">
              {draft.type}
            </span>
            <span className={`px-2 py-1 rounded-md font-medium ${
              draft.confidence_score > 0.8 ? 'bg-[#EAF3EA] text-[#3D663D]' : 
              draft.confidence_score > 0.5 ? 'bg-[#FDF3E1] text-[#997328]' : 'bg-[#FBEAEA] text-[#993333]'
            }`}>
              {Math.round(draft.confidence_score * 100)}% Match
            </span>
          </div>
        </div>
        <button 
          onClick={onReject}
          className="text-[#998877] hover:text-[#993333] transition-colors p-1"
          title="Reject Commitment"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 my-4">
        <div>
          <label className="block text-xs font-medium text-[#7A7771] mb-1">Estimated Minutes</label>
          <input
            type="number"
            className="w-full p-2 rounded bg-white border border-[#E5E0D8] text-[#2C2B29] focus:ring-1 focus:ring-[#B57C45] focus:outline-none"
            value={draft.estimated_minutes || ''}
            placeholder="e.g. 60"
            onChange={(e) => handleChange('estimated_minutes', e.target.value ? parseInt(e.target.value) : null)}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-[#7A7771] mb-1">Deadline (UTC)</label>
          <input
            type="datetime-local"
            className="w-full p-2 rounded bg-white border border-[#E5E0D8] text-[#2C2B29] focus:ring-1 focus:ring-[#B57C45] focus:outline-none"
            value={draft.deadline_at ? draft.deadline_at.slice(0, 16) : ''}
            onChange={(e) => handleChange('deadline_at', e.target.value ? new Date(e.target.value).toISOString() : null)}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-[#7A7771] mb-1">Importance (1-5)</label>
          <input
            type="range" min="1" max="5"
            className="w-full accent-[#B57C45]"
            value={draft.importance}
            onChange={(e) => handleChange('importance', parseInt(e.target.value))}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-[#7A7771] mb-1">Flexibility (1-5)</label>
          <input
            type="range" min="1" max="5"
            className="w-full accent-[#B57C45]"
            value={draft.flexibility}
            onChange={(e) => handleChange('flexibility', parseInt(e.target.value))}
          />
        </div>
      </div>

      {hasMissing && (
        <div className="bg-[#FDF8EE] border border-[#F2DEB6] text-[#997328] p-3 rounded-lg text-sm flex items-start gap-2 mb-4">
          <svg className="w-5 h-5 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div>
            <strong>Missing context:</strong> Please fill in {draft.missing_fields.join(', ')} for better planning.
          </div>
        </div>
      )}

      {draft.tasks.length > 0 && (
        <div className="mt-4 border-t border-[#E5E0D8] pt-3">
          <label className="block text-xs font-medium text-[#7A7771] mb-2">Detected Tasks</label>
          <ul className="space-y-1">
            {draft.tasks.map((task, idx) => (
              <li key={idx} className="text-sm text-[#4A4844] flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#B57C45]"></span>
                {task.title} {task.estimated_minutes ? <span className="text-xs text-[#998877]">({task.estimated_minutes}m)</span> : ''}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
