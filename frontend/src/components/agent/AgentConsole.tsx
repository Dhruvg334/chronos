import React, { useEffect, useState } from 'react';
import { apiFetch, apiUrl } from '../../lib/api';
import type { AgentTraceEvent } from '../../types/api';

interface AgentConsoleProps {
  agentRunId: string | null;
}

export const AgentConsole: React.FC<AgentConsoleProps> = ({ agentRunId }) => {
  const [traces, setTraces] = useState<AgentTraceEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!agentRunId) return;

    let cancelled = false;

    const pollTraces = async () => {
      try {
        const response = await apiFetch(apiUrl(`/api/v1/agent/runs/${agentRunId}/trace`));
        if (!response.ok) return;
        const data = await response.json();
        if (!cancelled) {
          setTraces(Array.isArray(data.events) ? data.events : []);
          setError(null);
        }
      } catch {
        if (!cancelled) setError('Trace updates are temporarily unavailable.');
      }
    };

    pollTraces();
    const intervalId = window.setInterval(pollTraces, 2000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [agentRunId]);

  if (!agentRunId) return null;

  const statusClass = (status: string) => {
    if (status === 'failed') return 'text-risk-atrisk';
    if (status === 'succeeded' || status === 'completed') return 'text-risk-stable';
    return 'text-text-muted';
  };

  return (
    <div className="max-h-64 w-full overflow-y-auto rounded-lg border border-warm-border bg-white p-4 text-sm shadow-inner">
      <div className="mb-2 flex items-center gap-2 font-bold text-accent-amber">
        <span className="h-2 w-2 rounded-full bg-accent-amber" />
        Agent trace {agentRunId.slice(0, 8)}
      </div>
      {error && <div className="mb-2 text-xs text-risk-atrisk">{error}</div>}
      <div className="space-y-1">
        {traces.length === 0 ? (
          <div className="text-text-muted italic">Waiting for trace events…</div>
        ) : (
          traces.map(trace => (
            <div key={trace.id} className="border-l-2 border-warm-border py-1 pl-3">
              <div className="flex flex-wrap items-center gap-3">
                <span className="shrink-0 text-text-muted">
                  {new Date(trace.created_at).toLocaleTimeString([], { hour12: false })}
                </span>
                <span className={statusClass(trace.status)}>{trace.step_name}</span>
                <span className="text-xs text-text-muted">{trace.status}</span>
              </div>
              {trace.explanation && <div className="mt-0.5 text-xs text-text-secondary">{trace.explanation}</div>}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
