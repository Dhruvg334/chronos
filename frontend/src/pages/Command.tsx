import { useState, useEffect } from 'react';
import { 
  Play, Check, SkipForward, AlertCircle, Clock, CheckCircle2, Circle
} from 'lucide-react';
import AppShell from '../components/layout/AppShell';
import ReflectionModal from '../components/command/ReflectionModal';
import SkipModal from '../components/command/SkipModal';
import type { SavedCommitment, CommitmentDetailResponse, NormalizedTimeSpineStage } from '../types/api';

export default function Command() {
  const [commitments, setCommitments] = useState<SavedCommitment[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<CommitmentDetailResponse | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [reflectionBlockId, setReflectionBlockId] = useState<string | null>(null);
  const [skipBlockId, setSkipBlockId] = useState<string | null>(null);
  
  // Create focus block state
  const [creatingBlock, setCreatingBlock] = useState(false);

  const fetchCommitments = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/commitments');
      if (!res.ok) throw new Error('Failed to load commitments');
      const data = await res.json();
      setCommitments(data);
      if (data.length > 0 && !selectedId) {
        setSelectedId(data[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Unable to load commitments');
    } finally {
      setLoadingList(false);
    }
  };

  const fetchDetail = async (id: string) => {
    setLoadingDetail(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/commitments/${id}`);
      if (!res.ok) throw new Error('Failed to load commitment detail');
      const data = await res.json();
      setDetail(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoadingDetail(false);
    }
  };

  useEffect(() => {
    fetchCommitments();
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
    const endAt = new Date(startAt.getTime() + 60 * 60 * 1000); // 1 hour default
    try {
      const res = await fetch('http://localhost:8000/api/v1/focus-blocks', {
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
      const res = await fetch(`http://localhost:8000/api/v1/focus-blocks/${blockId}/start`, { method: 'POST' });
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
      const res = await fetch(`http://localhost:8000/api/v1/focus-blocks/${reflectionBlockId}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        setReflectionBlockId(null);
        await fetchDetail(detail.id);
        await fetchCommitments();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSkipBlock = async (data: any) => {
    if (!skipBlockId || !detail) return;
    try {
      const res = await fetch(`http://localhost:8000/api/v1/focus-blocks/${skipBlockId}/skip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        setSkipBlockId(null);
        await fetchDetail(detail.id);
        await fetchCommitments();
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
      <div className="flex h-full gap-6">
        {/* Sidebar: Commitments List */}
        <div className="w-1/3 flex flex-col gap-4 border-r border-[#E5E0D8] pr-4 overflow-y-auto">
          <div>
            <h2 className="text-2xl font-extrabold text-[#2C2B29] mb-1">Commitments</h2>
            <p className="text-[#7A7771] text-sm">Select a commitment to open its canvas.</p>
          </div>
          {loadingList ? (
            <div className="text-[#7A7771]">Loading...</div>
          ) : error ? (
            <div className="text-[#993333] text-sm">{error}</div>
          ) : commitments.map(c => (
            <div 
              key={c.id} 
              onClick={() => setSelectedId(c.id)}
              className={`p-4 rounded-xl cursor-pointer transition-all border ${
                selectedId === c.id 
                  ? 'bg-white border-[#CC6633] shadow-md ring-1 ring-[#CC6633]' 
                  : 'bg-[#FAF9F6] border-[#E5E0D8] hover:bg-white hover:border-[#D1CCC2]'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-[#2C2B29] truncate pr-2">{c.title}</h3>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider whitespace-nowrap ${getRiskColor(c.risk_level)}`}>
                  {c.risk_level.replace('_', ' ')}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-[#7A7771]">
                <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {c.actual_minutes}/{c.estimated_minutes}m</span>
                <span>{c.progress_percent.toFixed(0)}% done</span>
              </div>
            </div>
          ))}
        </div>

        {/* Main Canvas */}
        <div className="w-2/3 flex flex-col overflow-y-auto pb-12 pr-2">
          {!detail ? (
            <div className="flex-1 flex items-center justify-center text-[#998877]">
              {loadingDetail ? 'Loading details...' : 'Select a commitment'}
            </div>
          ) : (
            <div className="space-y-6">
              {/* Header / Time Health Summary */}
              <div className="bg-white border border-[#E5E0D8] rounded-2xl p-6 shadow-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <h1 className="text-3xl font-extrabold text-[#2C2B29] mb-2">{detail.title}</h1>
                    <p className="text-[#7A7771]">{detail.description || 'No description provided.'}</p>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className={`px-3 py-1.5 rounded-lg text-sm font-bold uppercase tracking-wider ${getRiskColor(detail.risk_level)}`}>
                      {detail.risk_level.replace('_', ' ')} Risk ({detail.risk_score.toFixed(1)})
                    </span>
                    <span className="text-sm font-medium text-[#7A7771] mt-2">
                      Deadline: {detail.deadline_at ? new Date(detail.deadline_at).toLocaleDateString() : 'None'}
                    </span>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4 mt-6">
                  <div className="bg-[#FAF9F6] p-4 rounded-xl border border-[#E5E0D8]">
                    <div className="text-xs text-[#7A7771] font-semibold uppercase tracking-wider mb-1">Progress</div>
                    <div className="text-2xl font-bold text-[#2C2B29]">{detail.progress_percent.toFixed(0)}%</div>
                  </div>
                  <div className="bg-[#FAF9F6] p-4 rounded-xl border border-[#E5E0D8]">
                    <div className="text-xs text-[#7A7771] font-semibold uppercase tracking-wider mb-1">Time Spent</div>
                    <div className="text-2xl font-bold text-[#2C2B29]">{detail.actual_minutes} <span className="text-sm font-medium text-[#998877]">/ {detail.estimated_minutes} m</span></div>
                  </div>
                  <div className="bg-[#FAF9F6] p-4 rounded-xl border border-[#E5E0D8]">
                    <div className="text-xs text-[#7A7771] font-semibold uppercase tracking-wider mb-1">Next Action</div>
                    <div className="text-sm font-medium text-[#2C2B29] truncate mt-1">
                      {detail.tasks.find(t => t.status !== 'completed')?.title || 'All clear'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Layout Grid */}
              <div className="grid grid-cols-2 gap-6">
                
                {/* Time Spine Panel */}
                <div className="bg-[#FAF9F6] border border-[#E5E0D8] rounded-2xl p-6 shadow-sm">
                  <h3 className="text-lg font-bold text-[#2C2B29] mb-4 flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-[#3D663D]" />
                    Time Spine
                  </h3>
                  <div className="space-y-4">
                    {detail.time_spine_stages.length === 0 ? (
                      <div className="text-[#998877] text-sm">No spine generated yet.</div>
                    ) : (
                      <div className="relative">
                        <div className="absolute left-[9px] top-2 bottom-2 w-0.5 bg-[#E5E0D8]"></div>
                        {detail.time_spine_stages.map((stage: NormalizedTimeSpineStage) => (
                          <div key={stage.key} className="flex gap-4 relative z-10 mb-4 last:mb-0">
                            <div className="mt-1">
                              {stage.status === 'completed' ? (
                                <CheckCircle2 className="w-5 h-5 text-[#3D663D] bg-[#FAF9F6]" />
                              ) : stage.status === 'active' ? (
                                <Circle className="w-5 h-5 text-[#CC6633] fill-white bg-[#FAF9F6]" />
                              ) : (
                                <Circle className="w-5 h-5 text-[#D1CCC2] bg-[#FAF9F6]" />
                              )}
                            </div>
                            <div>
                              <div className={`font-semibold ${stage.status === 'completed' ? 'text-[#998877] line-through' : stage.status === 'active' ? 'text-[#CC6633]' : 'text-[#4A4844]'}`}>
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

                {/* Active Focus Console */}
                <div className="bg-white border border-[#E5E0D8] rounded-2xl p-6 shadow-sm flex flex-col">
                  <h3 className="text-lg font-bold text-[#2C2B29] mb-4 flex items-center gap-2">
                    <Play className="w-5 h-5 text-[#CC6633]" />
                    Active Focus Console
                  </h3>
                  
                  <div className="flex-1">
                    {detail.focus_blocks.filter(b => b.status === 'scheduled' || b.status === 'active').length === 0 ? (
                      <div className="text-center py-8">
                        <div className="w-12 h-12 bg-[#FDF3E1] rounded-full flex items-center justify-center mx-auto mb-3">
                          <Clock className="w-6 h-6 text-[#CC6633]" />
                        </div>
                        <p className="text-[#5C5A56] mb-4">No active focus block.</p>
                        <button 
                          onClick={handleCreateBlock}
                          disabled={creatingBlock}
                          className="px-4 py-2 bg-[#CC6633] text-white font-semibold rounded-lg hover:bg-[#B35929] transition-colors shadow-sm"
                        >
                          {creatingBlock ? 'Scheduling...' : 'Start Manual Focus Block'}
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {detail.focus_blocks.filter(b => b.status === 'scheduled' || b.status === 'active').map(block => (
                          <div key={block.id} className={`p-4 rounded-xl border ${block.status === 'active' ? 'border-[#CC6633] bg-[#FDF3E1]' : 'border-[#E5E0D8] bg-[#FAF9F6]'}`}>
                            <div className="flex justify-between items-start mb-2">
                              <div className="font-semibold text-[#2C2B29]">{block.title}</div>
                              <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${block.status === 'active' ? 'bg-[#CC6633] text-white' : 'bg-[#D1CCC2] text-[#4A4844]'}`}>
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
                                  className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-[#2C2B29] text-white text-sm font-medium rounded-lg hover:bg-black transition-colors"
                                >
                                  <Play className="w-4 h-4" /> Start
                                </button>
                              )}
                              {block.status === 'active' && (
                                <button 
                                  onClick={() => setReflectionBlockId(block.id)}
                                  className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-[#3D663D] text-white text-sm font-medium rounded-lg hover:bg-[#2F4D2F] transition-colors"
                                >
                                  <Check className="w-4 h-4" /> Complete
                                </button>
                              )}
                              <button 
                                onClick={() => setSkipBlockId(block.id)}
                                className="px-3 py-1.5 border border-[#D1CCC2] text-[#5C5A56] text-sm font-medium rounded-lg hover:bg-[#E5E0D8] transition-colors flex items-center justify-center"
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

              </div>
              
              {/* Activity Console / Reflections */}
              <div className="bg-[#FAF9F6] border border-[#E5E0D8] rounded-2xl p-6 shadow-sm">
                <h3 className="text-lg font-bold text-[#2C2B29] mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-[#5C5A56]" />
                  Activity & Reflections
                </h3>
                {detail.reflections.length === 0 ? (
                  <div className="text-[#998877] text-sm">No reflections recorded yet. Complete a focus block to add one.</div>
                ) : (
                  <div className="space-y-4">
                    {detail.reflections.map(refl => (
                      <div key={refl.id} className="bg-white p-4 rounded-xl border border-[#E5E0D8]">
                        <div className="flex justify-between items-start mb-2">
                          <div className="font-semibold text-[#2C2B29] capitalize">Status: {refl.completion_status}</div>
                          <div className="text-xs text-[#7A7771] bg-[#F4F2EC] px-2 py-1 rounded">
                            {refl.actual_minutes}m spent
                          </div>
                        </div>
                        <div className="text-sm text-[#5C5A56]">
                          Energy Level: {refl.energy_level}/5
                        </div>
                        {refl.notes && (
                          <div className="text-sm text-[#4A4844] mt-2 p-2 bg-[#FAF9F6] rounded border border-[#E5E0D8]">
                            "{refl.notes}"
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
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
