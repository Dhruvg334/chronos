import { useState } from 'react';

interface ReflectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: any) => Promise<void>;
  blockId: string;
}

export default function ReflectionModal({ isOpen, onClose, onSubmit }: ReflectionModalProps) {
  const [actualMinutes, setActualMinutes] = useState(30);
  const [energyLevel, setEnergyLevel] = useState(3);
  const [completionStatus] = useState('completed');
  const [progressUpdate, setProgressUpdate] = useState(0);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    await onSubmit({
      actual_minutes: actualMinutes,
      energy_level: energyLevel,
      completion_status: completionStatus,
      progress_percent_update: progressUpdate > 0 ? progressUpdate : undefined,
      notes: notes || undefined
    });
    setSubmitting(false);
  };

  return (
    <div className="fixed inset-0 bg-[#2C2B29]/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#FAF9F6] rounded-xl shadow-xl w-full max-w-md overflow-hidden border border-[#E5E0D8]">
        <div className="px-6 py-4 border-b border-[#E5E0D8]">
          <h2 className="text-xl font-bold text-[#2C2B29]">Focus Block Complete</h2>
          <p className="text-sm text-[#7A7771]">Reflect on your time and update progress.</p>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#4A4844] mb-1">Time Spent (minutes)</label>
            <input 
              type="number" 
              value={actualMinutes}
              onChange={(e) => setActualMinutes(Number(e.target.value))}
              className="w-full px-3 py-2 border border-[#D1CCC2] rounded-md bg-white focus:ring-[#CC6633] focus:border-[#CC6633]"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[#4A4844] mb-1">Energy Level (1-5)</label>
            <input 
              type="range" 
              min="1" max="5" 
              value={energyLevel}
              onChange={(e) => setEnergyLevel(Number(e.target.value))}
              className="w-full accent-[#CC6633]"
            />
            <div className="flex justify-between text-xs text-[#998877] mt-1">
              <span>Drained</span>
              <span>Energized</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#4A4844] mb-1">New Total Progress % (Optional)</label>
            <input 
              type="number" 
              placeholder="e.g. 50"
              value={progressUpdate || ''}
              onChange={(e) => setProgressUpdate(Number(e.target.value))}
              className="w-full px-3 py-2 border border-[#D1CCC2] rounded-md bg-white focus:ring-[#CC6633] focus:border-[#CC6633]"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[#4A4844] mb-1">Notes</label>
            <textarea 
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3 py-2 border border-[#D1CCC2] rounded-md bg-white focus:ring-[#CC6633] focus:border-[#CC6633]"
            ></textarea>
          </div>

          <div className="flex gap-3 justify-end mt-6">
            <button 
              type="button" 
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 text-[#5C5A56] font-medium hover:bg-[#E5E0D8] rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={submitting}
              className="px-4 py-2 bg-[#CC6633] text-white font-medium hover:bg-[#B35929] rounded-lg transition-colors shadow-sm disabled:opacity-50"
            >
              {submitting ? 'Saving...' : 'Complete Block'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
