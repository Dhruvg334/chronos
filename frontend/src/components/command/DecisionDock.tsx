import { useState, useEffect } from 'react';
import { Check, X, AlertTriangle, Zap, CheckCircle2 } from 'lucide-react';
import { apiUrl } from '../../lib/api';

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
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg shadow-black/20 mt-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-1.5 h-full bg-amber-500"></div>
      <div className="flex justify-between items-center mb-6 pl-2">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Zap className="w-5 h-5 text-amber-500" />
          Pending Approvals
        </h3>
        <button
          onClick={handleApproveAll}
          className="px-4 py-2 bg-emerald-600 text-white text-sm font-semibold rounded-lg hover:bg-emerald-500 transition-colors flex items-center gap-2 shadow-sm"
        >
          <CheckCircle2 className="w-4 h-4" /> Approve All
        </button>
      </div>

      <div className="space-y-4 pl-2">
        {proposals.map((p) => {
          const payload = p.payload_json;
          const isRescue = p.action_type === 'commitment_rescue';
          
          return (
            <div key={p.id} className={`border rounded-xl p-4 flex flex-col md:flex-row justify-between md:items-center gap-4 ${isRescue ? 'bg-rose-950/20 border-rose-900/50' : 'bg-slate-800/50 border-slate-700'}`}>
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <h4 className={`font-bold ${isRescue ? 'text-rose-500' : 'text-white'}`}>
                    {payload.title}
                  </h4>
                  {payload.risk_level && (
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-700 text-slate-300">
                      {payload.risk_level.replace('_', ' ')}
                    </span>
                  )}
                  <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded ${isRescue ? 'bg-rose-900 text-rose-200' : 'bg-emerald-900/50 text-emerald-400'}`}>
                    {payload.confidence_score}% Match
                  </span>
                  {isRescue && (
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-rose-600 text-white">
                      {payload.rescue_action_type?.replace(/_/g, ' ')}
                    </span>
                  )}
                </div>
                
                {isRescue ? (
                  <>
                    <div className="text-sm text-slate-300 mb-2 font-medium">
                      {payload.reason}
                    </div>
                    {payload.expected_impact && (
                      <div className="text-xs text-slate-400 mb-1">Impact: {payload.expected_impact}</div>
                    )}
                    {payload.tradeoff && (
                      <div className="text-xs text-slate-400 mb-2">Tradeoff: {payload.tradeoff}</div>
                    )}
                    {payload.draft_message && (
                      <div className="text-xs text-slate-300 bg-slate-900 p-3 rounded-lg border border-slate-800 mb-2 font-mono">
                        <div className="text-[10px] uppercase text-amber-500 font-bold mb-1">Draft only — not sent automatically</div>
                        {payload.draft_message}
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div className="text-xs text-slate-400 mb-2 font-medium">
                      {payload.start_at && new Date(payload.start_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })} 
                      {' '}to{' '} 
                      {payload.end_at && new Date(payload.end_at).toLocaleTimeString([], { timeStyle: 'short' })} 
                      {' '}({payload.duration_minutes}m)
                    </div>
                    <div className="text-sm text-slate-300 flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                      <span>{p.explanation}</span>
                    </div>
                  </>
                )}
              </div>
              <div className="flex md:flex-col gap-2 shrink-0">
                <button
                  onClick={() => handleApprove(p.id, p.action_type)}
                  className="flex-1 md:flex-none px-4 py-2 bg-emerald-600 text-white text-sm font-semibold rounded-lg hover:bg-emerald-500 transition-colors flex items-center justify-center gap-1 whitespace-nowrap"
                >
                  <Check className="w-4 h-4" /> Approve
                </button>
                <button
                  onClick={() => handleReject(p.id, p.action_type)}
                  className="flex-1 md:flex-none px-4 py-2 bg-transparent border border-slate-600 text-slate-300 text-sm font-semibold rounded-lg hover:bg-slate-800 transition-colors flex items-center justify-center gap-1 whitespace-nowrap"
                >
                  <X className="w-4 h-4" /> Reject
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
