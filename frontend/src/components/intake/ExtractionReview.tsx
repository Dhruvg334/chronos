import React, { useState } from 'react';
import { apiUrl, apiFetch as fetch, getApiErrorMessage } from '../../lib/api';
import type { CommitmentDraft, ApproveCommitmentsRequest } from '../../types/api';
import { CommitmentDraftCard } from './CommitmentDraftCard';
import { AgentConsole } from '../agent/AgentConsole';

interface ExtractionReviewProps {
  agentRunId: string;
  initialDrafts: CommitmentDraft[];
  onComplete: () => void;
}

export const ExtractionReview: React.FC<ExtractionReviewProps> = ({ agentRunId, initialDrafts, onComplete }) => {
  const [drafts, setDrafts] = useState<CommitmentDraft[]>(initialDrafts);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpdate = (index: number, updatedDraft: CommitmentDraft) => {
    const newDrafts = [...drafts];
    newDrafts[index] = updatedDraft;
    setDrafts(newDrafts);
  };

  const handleReject = (index: number) => {
    setDrafts(drafts.filter((_, i) => i !== index));
  };

  const handleApproveAll = async () => {
    if (drafts.length === 0) {
      setError("Cannot approve empty list.");
      return;
    }
    
    setIsSubmitting(true);
    setError(null);
    try {
      const payload: ApproveCommitmentsRequest = {
        agent_run_id: agentRunId,
        approved_drafts: drafts
      };

      const response = await fetch(apiUrl('/api/v1/ai/intake/approve'), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(await getApiErrorMessage(response, 'ChronOS could not save these commitments.'));
      }
      
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ChronOS could not save these commitments.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-text-primary mb-2">Review extracted commitments</h2>
        <p className="text-text-secondary">We've structured your brain dump. Please review and fill in missing fields before saving.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-4">
          {drafts.length === 0 ? (
            <div className="p-8 text-center text-text-muted border border-dashed border-warm-border rounded-xl bg-warm-ivory">
              No drafts remaining. 
            </div>
          ) : (
            drafts.map((draft, idx) => (
              <CommitmentDraftCard 
                key={idx} 
                draft={draft} 
                onUpdate={(d) => handleUpdate(idx, d)}
                onReject={() => handleReject(idx)}
              />
            ))
          )}
          
          <div className="pt-4 flex justify-end">
            <button 
              onClick={handleApproveAll}
              disabled={isSubmitting || drafts.length === 0}
              className="bg-accent-amber hover:bg-accent-terracotta disabled:bg-warm-border text-white px-6 py-2.5 rounded-lg font-medium transition-colors shadow-sm"
            >
              {isSubmitting ? 'Saving…' : `Approve ${drafts.length} commitments`}
            </button>
          </div>
          {error && <div className="text-risk-atrisk text-sm text-right mt-2">{error}</div>}
        </div>
        
        <div className="md:col-span-1">
          <div className="sticky top-6">
            <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-3">Agent status</h3>
            <AgentConsole agentRunId={agentRunId} />
          </div>
        </div>
      </div>
    </div>
  );
};
