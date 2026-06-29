import { useState, useEffect } from 'react';
import { Play, Check, SkipForward, AlertCircle, Clock, CheckCircle2, Circle } from 'lucide-react';
import { apiUrl, apiFetch as fetch } from '../lib/api';
import AppShell from '../components/layout/AppShell';
import ReflectionModal from '../components/command/ReflectionModal';
import SkipModal from '../components/command/SkipModal';
import { CalendarConnection } from '../components/command/CalendarConnection';
import DecisionDock from '../components/command/DecisionDock';
import { CommandHero } from '../components/command/CommandHero';
import { DailyCommandBrief, type CommandBriefData } from '../components/command/DailyCommandBrief';
import { DemoModeCard } from '../components/command/DemoModeCard';
import { EmptyState } from '../components/command/EmptyState';
import { InfoHint } from '../components/ui/InfoHint';
import type { SavedCommitment, CommitmentDetailResponse, NormalizedTimeSpineStage } from '../types/api';

export default function Command() {
  const [commitments, setCommitments] = useState<SavedCommitment[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<CommitmentDetailResponse | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  
  const [brief, setBrief] = useState<CommandBriefData | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [reflectionBlockId, setReflectionBlockId] = useState<string | null>(null);
  const [skipBlockId, setSkipBlockId] = useState<string | null>(null);
  const [creatingBlock, setCreatingBlock] = useState(false);
  const [dockKey, setDockKey] = useState(0);

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
      await fetch(apiUrl('/api/v1/scheduling/plan'), { method: 'POST' });
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
      await fetch(apiUrl('/api/v1/demo/load'), { method: 'POST' });
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
      case 'rescue_required': return 'bg-risk-critical text-white';
      case 'critical': return 'bg-risk-atrisk text-white';
      case 'at_risk': return 'bg-warm-border text-text-primary';
      case 'watch': return 'bg-warm-cream text-risk-watch';
      case 'stable': return 'bg-green-50 text-risk-stable';
      default: return 'bg-warm-border text-text-secondary';
    }
  };

  return (
    <AppShell>
      {/* max-w-5xl for wider layout to fix text truncation */}
      <div className="flex flex-col h-full overflow-y-auto pr-2 pb-12 max-w-5xl mx-auto">
        <CommandHero onAnalyze={handleRunAnalysis} isAnalyzing={isAnalyzing} />
        
        {commitments.length === 0 && !loadingList ? (
          <EmptyState onLoadDemo={async () => {
            if (window.confirm("This will add demo commitments to your local ChronOS workspace. It simulates a hackathon environment with a compromised timeline. It will overwrite any previous demo data. Proceed?")) {
              await handleLoadDemo();
            }
          }} />
        ) : (
          <>
            <DailyCommandBrief brief={brief} />
            <DecisionDock key={dockKey} onRefresh={refreshAll} />

            {rescueCandidates.length > 0 && (
              <div className="bg-warm-cream border-l-4 border-l-accent-terracotta border-y border-r border-warm-border rounded-r-xl p-5 mb-8 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                  <h3 className="text-base font-bold text-text-primary mb-1 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-risk-atrisk" /> 
                    Timeline needs attention
                    <InfoHint content="Commitments that may miss their deadline unless you change the plan." />
                  </h3>
                  <p className="text-sm text-text-secondary">
                    <strong>{rescueCandidates[0].title}</strong> may miss its deadline because {rescueCandidates[0]._rescue_reason?.toLowerCase() || 'remaining effort exceeds available focus time.'}
                  </p>
                </div>
                <button
                  onClick={() => handleRunRescue(rescueCandidates[0].id)}
                  disabled={runningRescue === rescueCandidates[0].id}
                  className="px-4 py-2 bg-white border border-warm-border text-accent-copper text-sm font-semibold rounded-lg hover:bg-warm-ivory transition-colors disabled:opacity-50 whitespace-nowrap shadow-sm"
                >
                  {runningRescue === rescueCandidates[0].id ? 'Generating...' : 'Review rescue options'}
                </button>
              </div>
            )}

            {/* Divider */}
            <hr className="border-warm-border my-8" />

            {/* Main Detail Canvas */}
            <div className="w-full flex flex-col gap-6">
              {!detail ? (
                <div className="flex-1 flex items-center justify-center text-text-muted bg-warm-ivory rounded-xl border border-warm-border border-dashed min-h-[200px]">
                  {loadingDetail ? 'Loading details...' : 'Select a commitment below to view its canvas'}
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Execution Workspace */}
                  <div className="bg-white border border-warm-border rounded-xl p-6 shadow-sm flex flex-col">
                    <div className="flex justify-between items-start mb-6">
                      <div>
                        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2">
                          <Play className="w-5 h-5 text-accent-amber" />
                          Execution Workspace
                        </h3>
                      </div>
                      <div className="text-right">
                        <h4 className="font-bold text-text-primary truncate max-w-[200px]" title={detail.title}>{detail.title}</h4>
                        <span className={`px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider ${getRiskColor(detail.risk_level)}`}>
                          {detail.risk_level.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                    <div className="flex-1">
                      {detail.focus_blocks.filter(b => b.status === 'scheduled' || b.status === 'active').length === 0 ? (
                        <div className="text-center py-6 bg-white rounded-lg border border-warm-border">
                          <p className="text-text-secondary mb-4 text-sm">No active focus block yet.</p>
                          <button 
                            onClick={handleCreateBlock}
                            disabled={creatingBlock}
                            className="px-4 py-2 bg-warm-ivory border border-warm-border text-text-primary text-sm font-semibold rounded-lg hover:bg-warm-border transition-colors shadow-sm"
                          >
                            {creatingBlock ? 'Scheduling...' : 'Create focus block'}
                          </button>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {detail.focus_blocks.filter(b => b.status === 'scheduled' || b.status === 'active').map(block => (
                            <div key={block.id} className={`p-4 rounded-xl border ${block.status === 'active' ? 'border-accent-amber bg-warm-cream' : 'border-warm-border bg-white'}`}>
                              <div className="flex justify-between items-start mb-2">
                                <div className="font-semibold text-text-primary text-sm">{block.title}</div>
                                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${block.status === 'active' ? 'bg-accent-amber text-white' : 'bg-warm-border text-text-secondary'}`}>
                                  {block.status}
                                </span>
                              </div>
                              <div className="text-xs text-text-muted mb-4">
                                {new Date(block.start_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - {new Date(block.end_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                              </div>
                              
                              <div className="flex gap-2">
                                {block.status === 'scheduled' && (
                                  <button 
                                    onClick={() => handleStartBlock(block.id)}
                                    className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-text-primary text-white text-xs font-medium rounded hover:bg-black transition-colors"
                                  >
                                    <Play className="w-3 h-3" /> Start
                                  </button>
                                )}
                                {block.status === 'active' && (
                                  <button 
                                    onClick={() => setReflectionBlockId(block.id)}
                                    className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-risk-stable text-white text-xs font-medium rounded hover:bg-green-700 transition-colors"
                                  >
                                    <Check className="w-3 h-3" /> Complete
                                  </button>
                                )}
                                <button 
                                  onClick={() => setSkipBlockId(block.id)}
                                  className="px-3 py-1.5 border border-warm-border text-text-secondary text-xs font-medium rounded hover:bg-warm-border transition-colors flex items-center justify-center"
                                >
                                  <SkipForward className="w-3 h-3" />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Time Spine */}
                  <div className="bg-white border border-warm-border rounded-xl p-6 shadow-sm">
                    <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
                      <CheckCircle2 className="w-5 h-5 text-risk-stable" />
                      Time Spine
                      <InfoHint content="The staged execution path ChronOS builds from intention to completion." />
                    </h3>
                    <div className="space-y-4 max-h-[250px] overflow-y-auto pr-2">
                      {detail.time_spine_stages.length === 0 ? (
                        <div className="text-text-muted text-sm bg-white p-4 rounded-lg border border-warm-border">No spine generated yet.</div>
                      ) : (
                        <div className="relative bg-white p-4 rounded-lg border border-warm-border">
                          <div className="absolute left-[25px] top-4 bottom-4 w-0.5 bg-warm-border"></div>
                          {detail.time_spine_stages.map((stage: NormalizedTimeSpineStage) => (
                            <div key={stage.key} className="flex gap-4 relative z-10 mb-4 last:mb-0">
                              <div className="mt-1">
                                {stage.status === 'completed' ? (
                                  <CheckCircle2 className="w-5 h-5 text-risk-stable bg-white" />
                                ) : stage.status === 'active' ? (
                                  <Circle className="w-5 h-5 text-accent-amber fill-white bg-white" />
                                ) : (
                                  <Circle className="w-5 h-5 text-warm-border bg-white" />
                                )}
                              </div>
                              <div>
                                <div className={`text-sm font-semibold ${stage.status === 'completed' ? 'text-text-muted line-through' : stage.status === 'active' ? 'text-accent-amber' : 'text-text-primary'}`}>
                                  {stage.label}
                                </div>
                                {stage.explanation && (
                                  <div className="text-xs text-text-secondary mt-0.5">{stage.explanation}</div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Divider */}
            <hr className="border-warm-border my-8" />

            {/* Lower Priority Sections */}
            <div className="space-y-8">
              <div>
                <h3 className="text-lg font-bold text-text-primary mb-4">Other Commitments</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {commitments.filter(c => c.id !== selectedId).map(c => (
                    <div 
                      key={c.id} 
                      onClick={() => setSelectedId(c.id)}
                      className="p-4 rounded-xl cursor-pointer transition-all border bg-white border-warm-border hover:border-text-muted hover:shadow-sm"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-sm text-text-primary truncate pr-2">{c.title}</h4>
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider whitespace-nowrap ${getRiskColor(c.risk_level)}`}>
                          {c.risk_level.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-text-muted">
                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {c.actual_minutes}/{c.estimated_minutes}m</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-bold text-text-primary mb-4">Connections</h3>
                <div className="space-y-4">
                  <CalendarConnection />
                  <DemoModeCard onLoadDemo={handleLoadDemo} />
                </div>
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
