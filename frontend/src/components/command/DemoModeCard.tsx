import { useState } from 'react';
import { Database, AlertCircle, Loader2 } from 'lucide-react';

interface DemoModeCardProps {
  onLoadDemo: () => Promise<void>;
}

export function DemoModeCard({ onLoadDemo }: DemoModeCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      await onLoadDemo();
    } finally {
      setIsLoading(false);
      setIsOpen(false);
    }
  };

  return (
    <div className="mt-6 border border-[#E5E0D8] rounded-xl overflow-hidden bg-white shadow-sm">
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[#FAF9F6] rounded-lg border border-[#E5E0D8]">
            <Database className="w-4 h-4 text-[#7A7771]" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[#2C2B29]">Judge Demo Mode</h3>
            <p className="text-xs text-[#5C5A56]">Populate a realistic last-minute scenario.</p>
          </div>
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="px-3 py-1.5 text-xs font-semibold text-[#5C5A56] bg-[#FAF9F6] border border-[#E5E0D8] hover:bg-[#E5E0D8] rounded-lg transition-colors"
        >
          Load Demo
        </button>
      </div>

      {isOpen && (
        <div className="p-4 border-t border-[#E5E0D8] bg-[#FAF9F6]">
          <div className="flex items-start gap-2 mb-4">
            <AlertCircle className="w-4 h-4 text-[#CC6633] shrink-0 mt-0.5" />
            <p className="text-xs text-[#5C5A56] leading-relaxed font-medium">
              This will add demo commitments to your local ChronOS workspace. It simulates a hackathon environment with a compromised timeline. It will overwrite any previous demo data.
            </p>
          </div>
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setIsOpen(false)}
              disabled={isLoading}
              className="px-3 py-1.5 text-xs font-semibold text-[#7A7771] hover:text-[#2C2B29] transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={isLoading}
              className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-white bg-[#B57C45] hover:bg-[#A36A36] rounded-lg transition-colors disabled:opacity-50"
            >
              {isLoading && <Loader2 className="w-3 h-3 animate-spin" />}
              Confirm Load Demo
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
