import { apiUrl } from '../../lib/api';
import React, { useState, useEffect } from 'react';
import type { AgentTraceEvent } from '../../types/api';

interface AgentConsoleProps {
  agentRunId: string | null;
}

export const AgentConsole: React.FC<AgentConsoleProps> = ({ agentRunId }) => {
  const [traces, setTraces] = useState<AgentTraceEvent[]>([]);

  useEffect(() => {
    if (!agentRunId) return;

    let cancelled = false;

    const pollTraces = async () => {
      try {
        const response = await fetch(apiUrl(`/api/v1/agent/runs/${agentRunId}/trace`));
        if (response.ok) {
          const data = await response.json();
          if (!cancelled) setTraces(Array.isArray(data.events) ? data.events : []);
        }
      } catch (error) {
        console.error('Error polling traces', error);
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
    if (status === 'failed') return 'text-red-400';
    if (status === 'succeeded' || status === 'completed') return 'text-green-400';
    return 'text-stone-300';
  };

  return (
    <div className="bg-stone-900 text-stone-300 font-mono text-sm p-4 rounded-lg shadow-inner max-h-64 overflow-y-auto w-full">
      <div className="text-amber-500 mb-2 font-bold flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
        Agent Trace: {agentRunId.slice(0, 8)}...
      </div>
      <div className="space-y-1">
        {traces.length === 0 ? (
          <div className="text-stone-500 italic">Waiting for backend trace events...</div>
        ) : (
          traces.map(trace => (
            <div key={trace.id} className="border-l-2 border-stone-700 pl-3 py-1">
              <div className="flex gap-3 items-center">
                <span className="text-stone-500 shrink-0">
                  {new Date(trace.created_at).toLocaleTimeString([], { hour12: false })}
                </span>
                <span className={statusClass(trace.status)}>{trace.step_name}</span>
                <span className="text-stone-500 text-xs">{trace.status}</span>
              </div>
              {trace.explanation && <div className="text-stone-400 text-xs mt-0.5">{trace.explanation}</div>}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
