import { useState } from 'react';

interface SkipModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: any) => Promise<void>;
  blockId: string;
}

export default function SkipModal({ isOpen, onClose, onSubmit }: SkipModalProps) {
  const [reason, setReason] = useState('blocked');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    await onSubmit({
      reason,
      notes: notes || undefined
    });
    setSubmitting(false);
  };

  return (
    <div className="fixed inset-0 bg-[#2C2B29]/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#FAF9F6] rounded-xl shadow-xl w-full max-w-md overflow-hidden border border-[#E5E0D8]">
        <div className="px-6 py-4 border-b border-[#E5E0D8]">
          <h2 className="text-xl font-bold text-[#2C2B29]">Skip Focus Block</h2>
          <p className="text-sm text-[#7A7771]">Skipping applies a small penalty to the risk score.</p>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#4A4844] mb-1">Reason</label>
            <select 
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 border border-[#D1CCC2] rounded-md bg-white focus:ring-[#CC6633] focus:border-[#CC6633]"
            >
              <option value="blocked">Blocked</option>
              <option value="interrupted">Interrupted</option>
              <option value="low_energy">Low Energy</option>
              <option value="postponed">Postponed</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#4A4844] mb-1">Details (Optional)</label>
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
              className="px-4 py-2 bg-[#993333] text-white font-medium hover:bg-[#802B2B] rounded-lg transition-colors shadow-sm disabled:opacity-50"
            >
              {submitting ? 'Skipping...' : 'Skip Block'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
