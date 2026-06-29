import { useState, useEffect } from 'react';
import { Check, X, Zap, CheckCircle2 } from 'lucide-react';
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

  if (loading) return <div className="text-sm text-[#7A7771]">Loading proposals...</div>;
  if (error) return <div className="text-sm text-[#993333]">{error}</div>;
  if (proposals.length === 0) return null; // Hide dock if nothing pending

  return (
    <div className="bg-white border border-[#E5E0D8] rounded-2xl p-6 shadow-sm mt-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-bold text-[#2C2B29] flex items-center gap-2">
            <Zap className="w-5 h-5 text-[#B57C45]" />
            Pending Approvals
            <InfoHint content="Suggested actions ChronOS prepared for you. Approving creates the action; rejecting dismisses it. Nothing here runs automatically." />
          </h3>
          <p className="text-sm text-[#5C5A56] mt-1">ChronOS only acts after you approve. These are suggested recovery actions.</p>
        </div>
        <button
          onClick={handleApproveAll}
          className="px-3 py-1.5 bg-[#FAF9F6] border border-[#E5E0D8] text-[#2C2B29] text-xs font-semibold rounded hover:bg-[#E5E0D8] transition-colors flex items-center gap-1.5 shadow-sm"
        >
          <CheckCircle2 className="w-3 h-3" /> Approve All
        </button>
      </div>

      <div className="space-y-3">
        {proposals.map((p) => {
          const payload = p.payload_json;
          const isRescue = p.action_type === 'commitment_rescue';
          
          return (
            <div key={p.id} className={`border rounded-lg p-3 flex flex-col md:flex-row justify-between md:items-center gap-3 ${isRescue ? 'bg-[#FFF5F5] border-[#F2D6D6]' : 'bg-[#FAF9F6] border-[#E5E0D8]'}`}>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <h4 className={`font-semibold text-sm truncate ${isRescue ? 'text-[#993333]' : 'text-[#2C2B29]'}`}>
                    {payload.title}
                  </h4>
                  {payload.risk_level && (
                    <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-[#E5E0D8] text-[#5C5A56]">
                      {payload.risk_level.replace('_', ' ')}
                    </span>
                  )}
                  {isRescue && (
                    <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-[#F2D6D6] text-[#993333]">
                      {payload.rescue_action_type?.replace(/_/g, ' ')}
                    </span>
                  )}
                </div>
                
                {isRescue ? (
                  <>
                    <div className="text-xs text-[#5C5A56] truncate">
                      {payload.reason}
                    </div>
                  </>
                ) : (
                  <div className="text-xs text-[#5C5A56] flex items-center gap-1.5 truncate">
                    {payload.start_at && new Date(payload.start_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })} 
                    {' '}to{' '} 
                    {payload.end_at && new Date(payload.end_at).toLocaleTimeString([], { timeStyle: 'short' })} 
                    {' '}({payload.duration_minutes}m)
                    <span className="text-[#D1CCC2] mx-1">|</span>
                    <span className="truncate">{p.explanation}</span>
                  </div>
                )}
              </div>
              
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => handleApprove(p.id, p.action_type)}
                  className="px-3 py-1 bg-[#3D663D] text-white text-xs font-semibold rounded hover:bg-[#2F4D2F] transition-colors flex items-center gap-1"
                >
                  <Check className="w-3 h-3" /> Approve
                </button>
                <button
                  onClick={() => handleReject(p.id, p.action_type)}
                  className="px-3 py-1 bg-transparent text-[#7A7771] hover:bg-[#E5E0D8] hover:text-[#5C5A56] text-xs font-semibold rounded transition-colors flex items-center gap-1"
                >
                  <X className="w-3 h-3" /> Reject
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
