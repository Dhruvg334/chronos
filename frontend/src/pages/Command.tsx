import { useState, useEffect } from 'react';
import { 
  Play, Check, SkipForward, AlertCircle, Clock, CheckCircle2, Circle
} from 'lucide-react';
import { apiUrl } from '../lib/api';
import AppShell from '../components/layout/AppShell';
import ReflectionModal from '../components/command/ReflectionModal';
import SkipModal from '../components/command/SkipModal';
import { CalendarConnection } from '../components/command/CalendarConnection';
import DecisionDock from '../components/command/DecisionDock';
import { CommandHero } from '../components/command/CommandHero';
import { DailyCommandBrief, type CommandBriefData } from '../components/command/DailyCommandBrief';
import { DemoModeCard } from '../components/command/DemoModeCard';
import { EmptyState } from '../components/command/EmptyState';
import type { SavedCommitment, CommitmentDetailResponse, NormalizedTimeSpineStage } from '../types/api';

export default function Command() {
  const [commitments, setCommitments] = useState<SavedCommitment[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<CommitmentDetailResponse | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  
  const [brief, setBrief] = useState<CommandBriefData | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Modal states
  const [reflectionBlockId, setReflectionBlockId] = useState<string | null>(null);
  const [skipBlockId, setSkipBlockId] = useState<string | null>(null);
  
  const [creatingBlock, setCreatingBlock] = useState(false);
  const [dockKey, setDockKey] = useState(0);

  // Rescue states
  const [rescueCandidates, setRescueCandidates] = useState<any[]>([]);
  const [runningRescue, setRunningRescue] = useState<string | null>(null);

  const refreshAll = async () => {
    await fetchCommitments();
    await fetchRescueCandidates();
    if (selectedId) await fetchDetail(selectedId);
    setDockKey(prev => prev + 1);
  };

  const fetchCommitments = async () => {
    try {
      const res = await fetch(apiUrl('/api/v1/commitments'));
      if (!res.ok) throw new Error('Failed to load commitments');
      const data = await res.json();
      setCommitments(data);
      if (data.length > 0 && !selectedId) {
        setSelectedId(data[0].id);
      }
    } catch (err: any) {
      console.error(err.message || 'Unable to load commitments');
    } finally {
      setLoadingList(false);
    }
  };

  const fetchDetail = async (id: string) => {
    setLoadingDetail(true);
    try {
      const res = await fetch(apiUrl(`/api/v1/commitments/${id}`));
      if (!res.ok) throw new Error('Failed to load commitment detail');
      const data = await res.json();
      setDetail(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const fetchRescueCandidates = async () => {
    try {
      const res = await fetch(apiUrl('/api/v1/rescue/candidates'));
      if (res.ok) {
        const data = await res.json();
        setRescueCandidates(data.candidates || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      const res = await fetch(apiUrl('/api/v1/command/analyze'), { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setBrief(data);
      }
      await refreshAll();
    } catch (err) {
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleLoadDemo = async () => {
    try {
      const res = await fetch(apiUrl('/api/v1/demo/load'), { method: 'POST' });
      if (!res.ok) throw new Error('Failed to load judge demo');
      await refreshAll();
      setBrief(null);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunRescue = async (cid: string) => {
    setRunningRescue(cid);
    try {
      const res = await fetch(apiUrl(`/api/v1/rescue/${cid}/plan`), { method: 'POST' });
      if (res.ok) {
        await refreshAll();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setRunningRescue(null);
    }
  };

  useEffect(() => {
    fetchCommitments();
    fetchRescueCandidates();
  }, []);

  useEffect(() => {
    if (selectedId) {
      fetchDetail(selectedId);
    }
  }, [selectedId]);

  const handleCreateBlock = async () => {
    if (!detail) return;
    setCreatingBlock(true);
    const startAt = new Date();
    const endAt = new Date(startAt.getTime() + 60 * 60 * 1000);
    try {
      const res = await fetch(apiUrl('/api/v1/focus-blocks'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          commitment_id: detail.id,
          title: `Focus on ${detail.title}`,
          start_at: startAt.toISOString(),
          end_at: endAt.toISOString(),
          block_type: 'deep_work'
        })
      });
      if (res.ok) {
        await fetchDetail(detail.id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setCreatingBlock(false);
    }
  };

  const handleStartBlock = async (blockId: string) => {
    try {
      const res = await fetch(apiUrl(`/api/v1/focus-blocks/${blockId}/start`), { method: 'POST' });
      if (res.ok && detail) {
        fetchDetail(detail.id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCompleteBlock = async (data: any) => {
    if (!reflectionBlockId || !detail) return;
    try {
      const res = await fetch(apiUrl(`/api/v1/focus-blocks/${reflectionBlockId}/complete`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        setReflectionBlockId(null);
        await refreshAll();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSkipBlock = async (data: any) => {
    if (!skipBlockId || !detail) return;
    try {
      const res = await fetch(apiUrl(`/api/v1/focus-blocks/${skipBlockId}/skip`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        setSkipBlockId(null);
        await refreshAll();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const getRiskColor = (level?: string) => {
    switch (level) {
      case 'rescue_required': return 'bg-rose-500 text-white';
      case 'critical': return 'bg-orange-500 text-white';
      case 'at_risk': return 'bg-slate-300 text-slate-800';
      case 'watch': return 'bg-amber-500 text-white';
      case 'stable': return 'bg-emerald-500 text-white';
      default: return 'bg-slate-700 text-slate-300';
    }
  };

  return (
    <AppShell>
      <div className="flex flex-col h-full overflow-y-auto pr-2 pb-12">
        <CommandHero onAnalyze={handleRunAnalysis} isAnalyzing={isAnalyzing} />
        
        {commitments.length === 0 && !loadingList ? (
          <EmptyState onLoadDemo={handleLoadDemo} />
        ) : (
          <>
            <DailyCommandBrief brief={brief} />
            
            {rescueCandidates.length > 0 && (
              <div className="bg-rose-950/30 border border-rose-900/50 rounded-xl p-6 mb-8 shadow-sm">
                <h3 className="text-lg font-bold text-rose-500 mb-2 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" /> Timeline compromised — {rescueCandidates.length} actions require rescue.
                </h3>
                <p className="text-sm text-slate-300 mb-4">
                  Your commitment "{rescueCandidates[0].title}" is critical because: {rescueCandidates[0]._rescue_reason.toLowerCase()}
                </p>
                <button
                  onClick={() => handleRunRescue(rescueCandidates[0].id)}
                  disabled={runningRescue === rescueCandidates[0].id}
                  className="px-6 py-2 bg-rose-600 text-white text-sm font-bold rounded-lg hover:bg-rose-500 transition-colors disabled:opacity-50"
                >
                  {runningRescue === rescueCandidates[0].id ? 'Generating Rescue Plan...' : 'Run Rescue Plan'}
                </button>
              </div>
            )}
            
            <div className="mb-8">
              <DecisionDock key={dockKey} onRefresh={refreshAll} />
            </div>

            <div className="flex gap-6 mt-4">
              {/* Sidebar: Commitments List & Connections */}
              <div className="w-1/3 flex flex-col gap-6">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <h2 className="text-xl font-bold text-white mb-4">Commitments</h2>
                  <div className="space-y-3">
                    {commitments.map(c => (
                      <div 
                        key={c.id} 
                        onClick={() => setSelectedId(c.id)}
                        className={`p-4 rounded-xl cursor-pointer transition-all border ${
                          selectedId === c.id 
                            ? 'bg-slate-800 border-amber-500 shadow-md ring-1 ring-amber-500/50' 
                            : 'bg-slate-800/50 border-slate-700 hover:bg-slate-800 hover:border-slate-600'
                        }`}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="font-semibold text-white truncate pr-2">{c.title}</h3>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider whitespace-nowrap ${getRiskColor(c.risk_level)}`}>
                            {c.risk_level.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-slate-400">
                          <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {c.actual_minutes}/{c.estimated_minutes}m</span>
                          <span>{c.progress_percent.toFixed(0)}% done</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <CalendarConnection />
                <DemoModeCard onLoadDemo={handleLoadDemo} />
              </div>

              {/* Main Detail Canvas */}
              <div className="w-2/3 flex flex-col gap-6">
                {!detail ? (
                  <div className="flex-1 flex items-center justify-center text-slate-500 bg-slate-900/50 rounded-xl border border-slate-800 border-dashed min-h-[400px]">
                    {loadingDetail ? 'Loading details...' : 'Select a commitment to view its canvas'}
                  </div>
                ) : (
                  <>
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
                      <div className="flex justify-between items-start">
                        <div>
                          <h1 className="text-3xl font-extrabold text-white mb-2">{detail.title}</h1>
                          <p className="text-slate-400">{detail.description || 'No description provided.'}</p>
                        </div>
                        <div className="flex flex-col items-end">
                          <span className={`px-3 py-1.5 rounded-lg text-sm font-bold uppercase tracking-wider ${getRiskColor(detail.risk_level)}`}>
                            {detail.risk_level.replace('_', ' ')} Risk
                          </span>
                          <span className="text-sm font-medium text-slate-400 mt-2">
                            Deadline: {detail.deadline_at ? new Date(detail.deadline_at).toLocaleDateString() : 'None'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                          <Play className="w-5 h-5 text-amber-500" />
                          Active Focus Console
                        </h3>
                        <div className="flex-1">
                          {detail.focus_blocks.filter(b => b.status === 'scheduled' || b.status === 'active').length === 0 ? (
                            <div className="text-center py-8">
                              <p className="text-slate-400 mb-4">No active focus block.</p>
                              <button 
                                onClick={handleCreateBlock}
                                disabled={creatingBlock}
                                className="px-4 py-2 bg-amber-600 text-white font-semibold rounded-lg hover:bg-amber-500 transition-colors shadow-sm"
                              >
                                {creatingBlock ? 'Scheduling...' : 'Start Manual Focus Block'}
                              </button>
                            </div>
                          ) : (
                            <div className="space-y-3">
                              {detail.focus_blocks.filter(b => b.status === 'scheduled' || b.status === 'active').map(block => (
                                <div key={block.id} className={`p-4 rounded-xl border ${block.status === 'active' ? 'border-amber-500/50 bg-amber-950/20' : 'border-slate-700 bg-slate-800/50'}`}>
                                  <div className="flex justify-between items-start mb-2">
                                    <div className="font-semibold text-white">{block.title}</div>
                                    <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${block.status === 'active' ? 'bg-amber-500 text-white' : 'bg-slate-700 text-slate-300'}`}>
                                      {block.status}
                                    </span>
                                  </div>
                                  <div className="text-xs text-slate-400 mb-4">
                                    {new Date(block.start_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - {new Date(block.end_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                  </div>
                                  
                                  <div className="flex gap-2">
                                    {block.status === 'scheduled' && (
                                      <button 
                                        onClick={() => handleStartBlock(block.id)}
                                        className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-slate-700 text-white text-sm font-medium rounded-lg hover:bg-slate-600 transition-colors"
                                      >
                                        <Play className="w-4 h-4" /> Start
                                      </button>
                                    )}
                                    {block.status === 'active' && (
                                      <button 
                                        onClick={() => setReflectionBlockId(block.id)}
                                        className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-500 transition-colors"
                                      >
                                        <Check className="w-4 h-4" /> Complete
                                      </button>
                                    )}
                                    <button 
                                      onClick={() => setSkipBlockId(block.id)}
                                      className="px-3 py-1.5 border border-slate-600 text-slate-400 text-sm font-medium rounded-lg hover:bg-slate-700 transition-colors flex items-center justify-center"
                                    >
                                      <SkipForward className="w-4 h-4" />
                                    </button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                          <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                          Time Spine
                        </h3>
                        <div className="space-y-4">
                          {detail.time_spine_stages.length === 0 ? (
                            <div className="text-slate-500 text-sm">No spine generated yet.</div>
                          ) : (
                            <div className="relative">
                              <div className="absolute left-[9px] top-2 bottom-2 w-0.5 bg-slate-800"></div>
                              {detail.time_spine_stages.map((stage: NormalizedTimeSpineStage) => (
                                <div key={stage.key} className="flex gap-4 relative z-10 mb-4 last:mb-0">
                                  <div className="mt-1">
                                    {stage.status === 'completed' ? (
                                      <CheckCircle2 className="w-5 h-5 text-emerald-500 bg-slate-900" />
                                    ) : stage.status === 'active' ? (
                                      <Circle className="w-5 h-5 text-amber-500 fill-slate-900 bg-slate-900" />
                                    ) : (
                                      <Circle className="w-5 h-5 text-slate-700 bg-slate-900" />
                                    )}
                                  </div>
                                  <div>
                                    <div className={`font-semibold ${stage.status === 'completed' ? 'text-slate-500 line-through' : stage.status === 'active' ? 'text-amber-500' : 'text-slate-300'}`}>
                                      {stage.label}
                                    </div>
                                    {stage.explanation && (
                                      <div className="text-xs text-slate-500 mt-0.5">{stage.explanation}</div>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </>
        )}
      </div>

      <ReflectionModal 
        isOpen={!!reflectionBlockId} 
        onClose={() => setReflectionBlockId(null)}
        onSubmit={handleCompleteBlock}
        blockId={reflectionBlockId || ''}
      />
      <SkipModal 
        isOpen={!!skipBlockId} 
        onClose={() => setSkipBlockId(null)}
        onSubmit={handleSkipBlock}
        blockId={skipBlockId || ''}
      />
    </AppShell>
  );
}
