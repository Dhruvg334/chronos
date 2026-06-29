import { useState, useEffect } from 'react';
import { Check, X, AlertTriangle, Zap, CheckCircle2 } from 'lucide-react';
import { apiUrl } from '../../lib/api';

interface Proposal {
  id: string;
  payload_json: {
    commitment_id: string;
    title: string;
    start_at: string;
    end_at: string;
    duration_minutes: number;
    risk_level: string;
    confidence_score: number;
    capacity_source: string;
    validation_status: string;
  };
  explanation: string;
}

export default function DecisionDock({ onRefresh }: { onRefresh: () => void }) {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProposals = async () => {
    try {
      const res = await fetch(apiUrl('/api/v1/scheduling/proposals'));
      if (!res.ok) throw new Error('Failed to fetch proposals');
      const data = await res.json();
      setProposals(data.proposals || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProposals();
  }, []);

  const handleApprove = async (id: string) => {
    try {
      await fetch(apiUrl(`/api/v1/scheduling/proposals/${id}/approve`), { method: 'POST' });
      await fetchProposals();
      onRefresh();
    } catch (err) {
      console.error(err);
    }
  };

  const handleReject = async (id: string) => {
    try {
      await fetch(apiUrl(`/api/v1/scheduling/proposals/${id}/reject`), { method: 'POST' });
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
    <div className="bg-white border border-[#CC6633] rounded-2xl p-6 shadow-md mt-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-1.5 h-full bg-[#CC6633]"></div>
      <div className="flex justify-between items-center mb-4 pl-2">
        <h3 className="text-lg font-bold text-[#2C2B29] flex items-center gap-2">
          <Zap className="w-5 h-5 text-[#CC6633]" />
          Decision Dock (Proposals)
        </h3>
        <button
          onClick={handleApproveAll}
          className="px-4 py-2 bg-[#2C2B29] text-white text-sm font-semibold rounded-lg hover:bg-black transition-colors flex items-center gap-2 shadow-sm"
        >
          <CheckCircle2 className="w-4 h-4" /> Approve All
        </button>
      </div>

      <div className="space-y-4 pl-2">
        {proposals.map((p) => {
          const payload = p.payload_json;
          return (
            <div key={p.id} className="bg-[#FAF9F6] border border-[#E5E0D8] rounded-xl p-4 flex justify-between items-center">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-1">
                  <h4 className="font-bold text-[#2C2B29]">{payload.title}</h4>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-[#D1CCC2] text-[#4A4844]">
                    {payload.risk_level.replace('_', ' ')}
                  </span>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-[#EAF3EA] text-[#3D663D]">
                    {payload.confidence_score}% Match
                  </span>
                </div>
                <div className="text-xs text-[#7A7771] mb-2 font-medium">
                  {new Date(payload.start_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })} 
                  {' '}to{' '} 
                  {new Date(payload.end_at).toLocaleTimeString([], { timeStyle: 'short' })} 
                  {' '}({payload.duration_minutes}m)
                </div>
                <div className="text-sm text-[#4A4844] flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-[#CC6633] shrink-0 mt-0.5" />
                  <span>{p.explanation}</span>
                </div>
              </div>
              <div className="flex flex-col gap-2 ml-4">
                <button
                  onClick={() => handleApprove(p.id)}
                  className="px-4 py-1.5 bg-[#3D663D] text-white text-sm font-semibold rounded hover:bg-[#2F4D2F] transition-colors flex items-center justify-center gap-1"
                >
                  <Check className="w-4 h-4" /> Approve
                </button>
                <button
                  onClick={() => handleReject(p.id)}
                  className="px-4 py-1.5 bg-transparent border border-[#993333] text-[#993333] text-sm font-semibold rounded hover:bg-[#FFF5F5] transition-colors flex items-center justify-center gap-1"
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
