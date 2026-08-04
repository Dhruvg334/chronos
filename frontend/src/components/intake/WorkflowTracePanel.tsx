import { useEffect, useState } from 'react';
import { apiFetch, apiUrl } from '../../lib/api';
import type { AgentTraceEvent } from '../../types/api';

export function WorkflowTracePanel({ runId }: { runId: string | null }) {
  const [traces, setTraces] = useState<AgentTraceEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!runId) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const response = await apiFetch(apiUrl(`/api/v1/workflows/${runId}/trace`));
        if (!response.ok) return;
        const data = await response.json();
        if (!cancelled) { setTraces(Array.isArray(data.events) ? data.events : []); setError(null); }
      } catch { if (!cancelled) setError('Status updates are temporarily unavailable.'); }
    };
    void poll(); const interval = window.setInterval(poll, 2000);
    return () => { cancelled = true; window.clearInterval(interval); };
  }, [runId]);
  if (!runId) return null;
  return <div className="max-h-64 w-full overflow-y-auto rounded-lg border border-line bg-surface p-4 text-sm shadow-inner">
    <div className="mb-2 flex items-center gap-2 font-bold text-accent-strong"><span className="h-2 w-2 rounded-full bg-accent" />Workflow status</div>
    {error && <div className="mb-2 text-xs text-danger">{error}</div>}
    <div className="space-y-1">{traces.length === 0 ? <div className="text-faint italic">Waiting for status updates…</div> : traces.map(trace =>
      <div key={trace.id} className="border-l-2 border-line py-1 pl-3"><div className="flex flex-wrap items-center gap-3"><span className="shrink-0 text-faint">{new Date(trace.created_at).toLocaleTimeString([], { hour12: false })}</span><span>{trace.step_name}</span><span className="text-xs text-faint">{trace.status}</span></div>{trace.explanation && <div className="mt-0.5 text-xs text-muted">{trace.explanation}</div>}</div>)}</div>
  </div>;
}
