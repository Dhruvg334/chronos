import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
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
  const queryClient = useQueryClient();
  const [drafts, setDrafts] = useState<CommitmentDraft[]>(initialDrafts);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newProjectTitle, setNewProjectTitle] = useState('');
  const projects = useQuery({ queryKey: ['projects'], queryFn: async () => { const response = await fetch(apiUrl('/api/v1/projects')); if (!response.ok) throw new Error(await getApiErrorMessage(response, 'Projects are unavailable.')); return response.json() as Promise<{ projects: Array<{ id: string; title: string }> }>; } });
  const createProject = useMutation({ mutationFn: async () => { const response = await fetch(apiUrl('/api/v1/projects'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: newProjectTitle, description: '', status: 'active', colour: 'accent' }) }); if (!response.ok) throw new Error(await getApiErrorMessage(response, 'The project could not be created.')); return response.json(); }, onSuccess: async () => { setNewProjectTitle(''); await queryClient.invalidateQueries({ queryKey: ['projects'] }); } });

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
        <h2 className="text-2xl font-semibold text-ink mb-2">Review extracted commitments</h2>
        <p className="text-muted">We've structured your brain dump. Please review and fill in missing fields before saving.</p>
        <div className="mt-4 flex max-w-xl gap-2"><input aria-label="New project title" className="field" placeholder="Create a project only if you choose" value={newProjectTitle} onChange={event => setNewProjectTitle(event.target.value)} /><button className="button-secondary shrink-0" disabled={!newProjectTitle.trim() || createProject.isPending} onClick={() => createProject.mutate()}>{createProject.isPending ? 'Creating…' : 'Create project'}</button></div>
        {createProject.isError && <p role="alert" className="mt-2 text-sm text-danger">{createProject.error.message}</p>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-4">
          {drafts.length === 0 ? (
            <div className="p-8 text-center text-faint border border-dashed border-line rounded-xl bg-canvas">
              No drafts remaining. 
            </div>
          ) : (
            drafts.map((draft, idx) => (
              <CommitmentDraftCard 
                key={idx} 
                draft={draft} 
                onUpdate={(d) => handleUpdate(idx, d)}
                onReject={() => handleReject(idx)}
                projects={projects.data?.projects}
              />
            ))
          )}
          
          <div className="pt-4 flex justify-end">
            <button 
              onClick={handleApproveAll}
              disabled={isSubmitting || drafts.length === 0}
              className="bg-accent hover:bg-accent-strong disabled:bg-line text-white px-6 py-2.5 rounded-lg font-medium transition-colors shadow-sm"
            >
              {isSubmitting ? 'Saving…' : `Approve ${drafts.length} planning items`}
            </button>
          </div>
          {error && <div className="text-danger text-sm text-right mt-2">{error}</div>}
        </div>
        
        <div className="md:col-span-1">
          <div className="sticky top-6">
            <h3 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">Agent status</h3>
            <AgentConsole agentRunId={agentRunId} />
          </div>
        </div>
      </div>
    </div>
  );
};
