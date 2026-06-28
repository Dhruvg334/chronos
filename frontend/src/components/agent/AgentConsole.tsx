import React, { useState, useEffect } from 'react';
import { AgentTraceEvent } from '../../types/api';

interface AgentConsoleProps {
  agentRunId: string | null;
}

export const AgentConsole: React.FC<AgentConsoleProps> = ({ agentRunId }) => {
  const [traces, setTraces] = useState<AgentTraceEvent[]>([]);

  // Simple polling mechanism for trace events
  useEffect(() => {
    if (!agentRunId) return;

    const intervalId = setInterval(async () => {
      try {
        // In a real app this would hit GET /api/v1/agent/runs/{agentRunId}/trace
        // We will simulate it picking up traces if the endpoint doesn't exist yet
        // since the trace polling endpoint wasn't explicitly in the Phase 2 backend requirements,
        // but it was requested to "show real trace events from the backend... polling is acceptable".
        // Wait, I should add a trace polling endpoint or just assume it exists. 
        // Let's implement the endpoint in backend/app/api/v1/agent.py shortly.
        const response = await fetch(`http://localhost:8000/api/v1/agent/runs/${agentRunId}/trace`);
        if (response.ok) {
          const data = await response.json();
          setTraces(data.events);
        }
      } catch (error) {
        console.error("Error polling traces", error);
      }
    }, 2000);

    return () => clearInterval(intervalId);
  }, [agentRunId]);

  if (!agentRunId) return null;

  return (
    <div className="bg-stone-900 text-stone-300 font-mono text-sm p-4 rounded-lg shadow-inner max-h-64 overflow-y-auto w-full">
      <div className="text-amber-500 mb-2 font-bold flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
        Agent Trace: {agentRunId.slice(0, 8)}...
      </div>
      <div className="space-y-1">
        {traces.length === 0 ? (
          <div className="text-stone-500 italic">Initializing agent run...</div>
        ) : (
          traces.map(trace => (
            <div key={trace.id} className="flex gap-4 border-l-2 border-stone-700 pl-3 py-1">
              <span className="text-stone-500 shrink-0">
                {new Date(trace.created_at).toLocaleTimeString([], { hour12: false })}
              </span>
              <span className={
                trace.event_type.includes('failed') ? "text-red-400" :
                trace.event_type.includes('succeeded') || trace.event_type.includes('completed') ? "text-green-400" :
                "text-stone-300"
              }>
                {trace.event_type}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
