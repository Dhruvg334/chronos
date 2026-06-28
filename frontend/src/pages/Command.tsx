import { useState, useEffect } from 'react';
import AppShell from '../components/layout/AppShell';
import type { SavedCommitment, TimeSpineCheckpoint } from '../types/api';

export default function Command() {
  const [commitments, setCommitments] = useState<SavedCommitment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/commitments')
      .then(res => {
        if (!res.ok) throw new Error('Failed to load commitments');
        return res.json();
      })
      .then(data => {
        if (Array.isArray(data)) setCommitments(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError(err.message || 'Unable to load commitments');
        setLoading(false);
      });
  }, []);

  const renderSpine = (checkpoints: TimeSpineCheckpoint[] = []) => {
    if (checkpoints.length === 0) {
      return <div className="text-sm text-[#998877]">No time spine available yet.</div>;
    }

    return checkpoints.map((checkpoint, i) => (
      <div key={`${checkpoint.id}-${i}`} className="flex items-center gap-2 text-sm text-[#4A4844]">
        <span className={`w-2 h-2 rounded-full ${checkpoint.status === 'completed' ? 'bg-[#3D663D]' : 'bg-[#D1CCC2]'}`}></span>
        <span className={checkpoint.status === 'completed' ? 'line-through text-[#998877]' : ''}>{checkpoint.label}</span>
      </div>
    ));
  };

  return (
    <AppShell>
      <div className="flex flex-col h-full space-y-6">
        <div>
          <h2 className="text-3xl font-extrabold text-[#2C2B29] mb-2">Command Canvas</h2>
          <p className="text-[#5C5A56]">Your structured commitments and their time spines.</p>
        </div>

        {loading ? (
          <div className="text-[#7A7771]">Loading commitments...</div>
        ) : error ? (
          <div className="p-4 text-[#993333] border border-[#F2C2B6] rounded-xl bg-[#FBEAEA]">{error}</div>
        ) : commitments.length === 0 ? (
          <div className="p-8 text-center text-[#7A7771] border border-dashed border-[#D1CCC2] rounded-xl bg-[#FAF9F6]">
            No active commitments found. Go to Inbox to compile some.
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {commitments.map(c => {
              const checkpoints = c.time_spines?.[0]?.spine_json ?? [];
              return (
                <div key={c.id} className="bg-[#FAF9F6] border border-[#E5E0D8] rounded-xl p-5 shadow-sm">
                  <div className="flex justify-between items-start mb-3 gap-3">
                    <h3 className="text-xl font-semibold text-[#2C2B29]">{c.title}</h3>
                    <span className={`px-2 py-1 rounded-md text-xs font-bold uppercase whitespace-nowrap ${
                      c.risk_level === 'rescue_required' ? 'bg-[#993333] text-white' :
                      c.risk_level === 'critical' ? 'bg-[#CC6633] text-white' :
                      c.risk_level === 'at_risk' ? 'bg-[#D1CCC2] text-[#2C2B29]' :
                      c.risk_level === 'watch' ? 'bg-[#FDF3E1] text-[#997328]' :
                      'bg-[#EAF3EA] text-[#3D663D]'
                    }`}>
                      {c.risk_level.replace('_', ' ')}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm text-[#7A7771] mb-4">
                    <div><strong>Effort:</strong> {c.estimated_minutes ?? '?'} mins</div>
                    <div><strong>Deadline:</strong> {c.deadline_at ? new Date(c.deadline_at).toLocaleDateString() : 'None'}</div>
                    <div><strong>Risk score:</strong> {Math.round(c.risk_score ?? 0)}</div>
                    <div><strong>Type:</strong> {c.type.replace('_', ' ')}</div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-[#E5E0D8]">
                    <h4 className="text-xs font-semibold text-[#5C5A56] uppercase tracking-wider mb-2">Basic Time Spine</h4>
                    <div className="flex flex-col gap-2">{renderSpine(checkpoints)}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}
