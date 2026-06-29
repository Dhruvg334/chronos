import { useState, useEffect } from 'react';
import { Play, Check, SkipForward, AlertCircle, Clock, CheckCircle2, Circle } from 'lucide-react';
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
    // If called from EmptyState, it should act just like DemoModeCard confirmation
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
      case 'rescue_required': return 'bg-[#993333] text-white';
      case 'critical': return 'bg-[#CC6633] text-white';
      case 'at_risk': return 'bg-[#D1CCC2] text-[#2C2B29]';
      case 'watch': return 'bg-[#FDF3E1] text-[#997328]';
      case 'stable': return 'bg-[#EAF3EA] text-[#3D663D]';
      default: return 'bg-[#E5E0D8] text-[#5C5A56]';
    }
  };

  return (
    <AppShell>
      <div className="flex flex-col h-full overflow-y-auto pr-2 pb-12 max-w-5xl mx-auto">
        <CommandHero onAnalyze={handleRunAnalysis} isAnalyzing={isAnalyzing} onLoadDemo={handleLoadDemo} />
        
        {commitments.length === 0 && !loadingList ? (
          <EmptyState onLoadDemo={async () => {
            if (window.confirm("This will add demo commitments to your local ChronOS workspace. It simulates a hackathon environment with a compromised timeline. It will overwrite any previous demo data. Proceed?")) {
              await handleLoadDemo();
            }
          }} />
        ) : (
          <>
            <DailyCommandBrief brief={brief} />
            
            <div className="mb-8">
              <DecisionDock key={dockKey} onRefresh={refreshAll} />
            </div>

            {rescueCandidates.length > 0 && (
              <div className="bg-[#FFF8F0] border-l-4 border-l-[#CC6633] border-y border-r border-[#E5E0D8] rounded-r-xl p-5 mb-8 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                  <h3 className="text-base font-bold text-[#2C2B29] mb-1 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-[#CC6633]" /> 
                    Timeline needs attention
                    <InfoHint content="Commitments that may miss their deadline unless you change the plan." />
                  </h3>
                  <p className="text-sm text-[#5C5A56]">
                    <strong>{rescueCandidates[0].title}</strong> may miss its deadline because {rescueCandidates[0]._rescue_reason.toLowerCase()}
                  </p>
                </div>
                <button
                  onClick={() => handleRunRescue(rescueCandidates[0].id)}
                  disabled={runningRescue === rescueCandidates[0].id}
                  className="px-4 py-2 bg-white border border-[#CC6633] text-[#CC6633] text-sm font-bold rounded-lg hover:bg-[#FFF5F5] transition-colors disabled:opacity-50 whitespace-nowrap shadow-sm"
                >
                  {runningRescue === rescueCandidates[0].id ? 'Generating...' : 'Review rescue options'}
                </button>
              </div>
            )}

            {/* Main Detail Canvas */}
            <div className="w-full flex flex-col gap-6">
              {!detail ? (
                <div className="flex-1 flex items-center justify-center text-[#7A7771] bg-[#FAF9F6] rounded-xl border border-[#E5E0D8] border-dashed min-h-[200px]">
                  {loadingDetail ? 'Loading details...' : 'Select a commitment below to view its canvas'}
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-white border border-[#E5E0D8] rounded-2xl p-6 shadow-sm flex flex-col">
                      <div className="flex justify-between items-start mb-6">
                        <div>
                          <h3 className="text-lg font-bold text-[#2C2B29] flex items-center gap-2">
                            <Play className="w-5 h-5 text-[#B57C45]" />
                            Active Focus Console
                          </h3>
                        </div>
                        <div className="text-right">
                          <h4 className="font-bold text-[#2C2B29] truncate max-w-[200px]" title={detail.title}>{detail.title}</h4>
                          <span className={`px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider ${getRiskColor(detail.risk_level)}`}>
                            {detail.risk_level.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                      <div className="flex-1">
                        {detail.focus_blocks.filter(b => b.status === 'scheduled' || b.status === 'active').length === 0 ? (
                          <div className="text-center py-6">
                            <p className="text-[#5C5A56] mb-4 text-sm">No active focus block.</p>
                            <button 
                              onClick={handleCreateBlock}
                              disabled={creatingBlock}
                              className="px-4 py-2 bg-[#FAF9F6] border border-[#E5E0D8] text-[#2C2B29] text-sm font-semibold rounded-lg hover:bg-[#E5E0D8] transition-colors shadow-sm"
                            >
                              {creatingBlock ? 'Scheduling...' : 'Start Manual Focus Block'}
                            </button>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            {detail.focus_blocks.filter(b => b.status === 'scheduled' || b.status === 'active').map(block => (
                              <div key={block.id} className={`p-4 rounded-xl border ${block.status === 'active' ? 'border-[#CC6633] bg-[#FDF3E1]' : 'border-[#E5E0D8] bg-[#FAF9F6]'}`}>
                                <div className="flex justify-between items-start mb-2">
                                  <div className="font-semibold text-[#2C2B29] text-sm">{block.title}</div>
                                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${block.status === 'active' ? 'bg-[#CC6633] text-white' : 'bg-[#D1CCC2] text-[#4A4844]'}`}>
                                    {block.status}
                                  </span>
                                </div>
                                <div className="text-xs text-[#7A7771] mb-4">
                                  {new Date(block.start_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - {new Date(block.end_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                </div>
                                
                                <div className="flex gap-2">
                                  {block.status === 'scheduled' && (
                                    <button 
                                      onClick={() => handleStartBlock(block.id)}
                                      className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-[#2C2B29] text-white text-xs font-medium rounded hover:bg-black transition-colors"
                                    >
                                      <Play className="w-3 h-3" /> Start
                                    </button>
                                  )}
                                  {block.status === 'active' && (
                                    <button 
                                      onClick={() => setReflectionBlockId(block.id)}
                                      className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-[#3D663D] text-white text-xs font-medium rounded hover:bg-[#2F4D2F] transition-colors"
                                    >
                                      <Check className="w-3 h-3" /> Complete
                                    </button>
                                  )}
                                  <button 
                                    onClick={() => setSkipBlockId(block.id)}
                                    className="px-3 py-1.5 border border-[#D1CCC2] text-[#5C5A56] text-xs font-medium rounded hover:bg-[#E5E0D8] transition-colors flex items-center justify-center"
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

                    <div className="bg-white border border-[#E5E0D8] rounded-2xl p-6 shadow-sm">
                      <h3 className="text-lg font-bold text-[#2C2B29] mb-4 flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-[#3D663D]" />
                        Time Spine
                        <InfoHint content="The staged execution path ChronOS builds from intention to completion." />
                      </h3>
                      <div className="space-y-4 max-h-[250px] overflow-y-auto pr-2">
                        {detail.time_spine_stages.length === 0 ? (
                          <div className="text-[#7A7771] text-sm">No spine generated yet.</div>
                        ) : (
                          <div className="relative">
                            <div className="absolute left-[9px] top-2 bottom-2 w-0.5 bg-[#E5E0D8]"></div>
                            {detail.time_spine_stages.map((stage: NormalizedTimeSpineStage) => (
                              <div key={stage.key} className="flex gap-4 relative z-10 mb-4 last:mb-0">
                                <div className="mt-1">
                                  {stage.status === 'completed' ? (
                                    <CheckCircle2 className="w-5 h-5 text-[#3D663D] bg-white" />
                                  ) : stage.status === 'active' ? (
                                    <Circle className="w-5 h-5 text-[#B57C45] fill-white bg-white" />
                                  ) : (
                                    <Circle className="w-5 h-5 text-[#D1CCC2] bg-white" />
                                  )}
                                </div>
                                <div>
                                  <div className={`text-sm font-semibold ${stage.status === 'completed' ? 'text-[#998877] line-through' : stage.status === 'active' ? 'text-[#B57C45]' : 'text-[#4A4844]'}`}>
                                    {stage.label}
                                  </div>
                                  {stage.explanation && (
                                    <div className="text-xs text-[#7A7771] mt-0.5">{stage.explanation}</div>
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

            <div className="mt-12 pt-8 border-t border-[#E5E0D8]">
              <h3 className="text-lg font-bold text-[#2C2B29] mb-4">Other Commitments</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {commitments.filter(c => c.id !== selectedId).map(c => (
                  <div 
                    key={c.id} 
                    onClick={() => setSelectedId(c.id)}
                    className="p-3 rounded-xl cursor-pointer transition-all border bg-white border-[#E5E0D8] hover:border-[#D1CCC2] hover:shadow-sm"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-sm text-[#2C2B29] truncate pr-2">{c.title}</h4>
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider whitespace-nowrap ${getRiskColor(c.risk_level)}`}>
                        {c.risk_level.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-[#7A7771]">
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {c.actual_minutes}/{c.estimated_minutes}m</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-8">
              <h3 className="text-lg font-bold text-[#2C2B29] mb-4">System Console</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <CalendarConnection />
                <DemoModeCard onLoadDemo={handleLoadDemo} />
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
