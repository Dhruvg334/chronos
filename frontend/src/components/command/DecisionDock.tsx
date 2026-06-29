import { useState, useEffect } from 'react';
import { Check, X, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import { apiUrl } from '../../lib/api';
import { InfoHint } from '../ui/InfoHint';

interface Proposal {
  id: string;
  action_type?: string;
  payload_json: {
    commitment_id: string;
    title: string;
    start_at?: string;
    end_at?: string;
    duration_minutes?: number;
    risk_level?: string;
    confidence_score: number;
    capacity_source?: string;
    validation_status: string;
    rescue_action_type?: string;
    reason?: string;
    urgency?: string;
    expected_impact?: string;
    tradeoff?: string;
    draft_message?: string;
  };
  explanation: string;
}

export default function DecisionDock({ onRefresh }: { onRefresh: () => void }) {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const fetchProposals = async () => {
    try {
      const [schedRes, rescueRes] = await Promise.all([
        fetch(apiUrl('/api/v1/scheduling/proposals')),
        fetch(apiUrl('/api/v1/rescue/plans'))
      ]);
      
      let allProposals: Proposal[] = [];
      if (schedRes.ok) {
        const data = await schedRes.json();
        allProposals = allProposals.concat(data.proposals || []);
      }
      if (rescueRes.ok) {
        const data = await rescueRes.json();
        allProposals = allProposals.concat(data.proposals || []);
      }
      
      setProposals(allProposals);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProposals();
  }, []);

  const handleApprove = async (id: string, actionType?: string) => {
    try {
      const path = actionType === 'commitment_rescue' 
        ? `/api/v1/rescue/proposals/${id}/approve`
        : `/api/v1/scheduling/proposals/${id}/approve`;
      await fetch(apiUrl(path), { method: 'POST' });
      await fetchProposals();
      onRefresh();
    } catch (err) {
      console.error(err);
    }
  };

  const handleReject = async (id: string, actionType?: string) => {
    try {
      const path = actionType === 'commitment_rescue' 
        ? `/api/v1/rescue/proposals/${id}/reject`
        : `/api/v1/scheduling/proposals/${id}/reject`;
      await fetch(apiUrl(path), { method: 'POST' });
      await fetchProposals();
    } catch (err) {
      console.error(err);
    }
  };

  const handleApproveAll = async () => {
    try {
      await fetch(apiUrl('/api/v1/scheduling/proposals/approve-all'), { method: 'POST' });
      await fetchProposals();
      onRefresh();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div className="text-sm text-text-muted">Loading proposals...</div>;
  if (error) return <div className="text-sm text-risk-critical">{error}</div>;
  if (proposals.length === 0) return null; // Hide dock if nothing pending

  const numRescue = proposals.filter(p => p.action_type === 'commitment_rescue').length;
  const numFocus = proposals.length - numRescue;

  // Group proposals by commitment title
  const groupedProposals = proposals.reduce((acc, p) => {
    const title = p.payload_json.title;
    if (!acc[title]) acc[title] = [];
    acc[title].push(p);
    return acc;
  }, {} as Record<string, Proposal[]>);

  return (
    <div className="bg-warm-cream border border-warm-border rounded-xl p-6 shadow-sm mb-8">
      {/* Summary View */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-text-primary flex items-center gap-2">
            <Zap className="w-5 h-5 text-accent-amber" />
            {proposals.length} suggested {proposals.length === 1 ? 'action' : 'actions'} waiting
            <InfoHint content="ChronOS only acts after you approve. Nothing here runs automatically." />
          </h3>
          <p className="text-sm text-text-secondary mt-1">
            {numRescue > 0 && `${numRescue} rescue block${numRescue > 1 ? 's' : ''}`}
            {numRescue > 0 && numFocus > 0 && ', '}
            {numFocus > 0 && `${numFocus} focus block${numFocus > 1 ? 's' : ''}`}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="px-4 py-2 bg-white border border-warm-border text-text-primary text-sm font-semibold rounded-lg hover:bg-warm-ivory transition-colors flex items-center gap-2 shadow-sm"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            Review suggestions
          </button>
          <button
            onClick={handleApproveAll}
            className="px-4 py-2 bg-transparent text-text-muted hover:text-text-primary hover:bg-warm-border/50 text-sm font-semibold rounded-lg transition-colors"
          >
            Approve All
          </button>
        </div>
      </div>

      {/* Expanded View */}
      {expanded && (
        <div className="mt-6 space-y-6 border-t border-warm-border pt-6">
          {Object.entries(groupedProposals).map(([title, groupProposals]) => (
            <div key={title} className="space-y-3">
              <h4 className="font-bold text-text-primary text-sm pl-1">{title}</h4>
              <div className="space-y-2">
                {groupProposals.map((p) => {
                  const payload = p.payload_json;
                  const isRescue = p.action_type === 'commitment_rescue';
                  
                  return (
                    <div key={p.id} className="bg-white border border-warm-border rounded-lg p-3 flex flex-col md:flex-row justify-between md:items-center gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2 mb-1">
                          <span className={`text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded ${isRescue ? 'bg-red-50 text-risk-critical' : 'bg-warm-surface text-text-secondary'}`}>
                            {isRescue ? payload.rescue_action_type?.replace(/_/g, ' ') : 'Focus Block'}
                          </span>
                        </div>
                        
                        {isRescue ? (
                          <div className="text-xs text-text-secondary truncate">
                            {payload.reason}
                          </div>
                        ) : (
                          <div className="text-xs text-text-secondary flex items-center gap-1.5 truncate">
                            {payload.start_at && new Date(payload.start_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })} 
                            {' '}to{' '} 
                            {payload.end_at && new Date(payload.end_at).toLocaleTimeString([], { timeStyle: 'short' })} 
                            {' '}({payload.duration_minutes}m)
                            <span className="text-warm-border mx-1">|</span>
                            <span className="truncate">{p.explanation}</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => handleApprove(p.id, p.action_type)}
                          className="px-3 py-1 bg-risk-stable text-white text-xs font-semibold rounded hover:bg-green-700 transition-colors flex items-center gap-1"
                        >
                          <Check className="w-3 h-3" /> Approve
                        </button>
                        <button
                          onClick={() => handleReject(p.id, p.action_type)}
                          className="px-3 py-1 bg-transparent text-text-muted hover:bg-warm-surface hover:text-text-primary text-xs font-semibold rounded transition-colors flex items-center gap-1"
                        >
                          <X className="w-3 h-3" /> Reject
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
