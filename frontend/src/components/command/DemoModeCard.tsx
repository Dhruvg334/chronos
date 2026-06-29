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
    <div className="mt-8 border border-slate-800 rounded-xl overflow-hidden bg-slate-900/30">
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-slate-800 rounded-lg">
            <Database className="w-5 h-5 text-slate-400" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-white">Judge Demo Mode</h3>
            <p className="text-xs text-slate-500">Instantly populate a realistic last-minute scenario.</p>
          </div>
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
        >
          Load Judge Demo
        </button>
      </div>

      {isOpen && (
        <div className="p-4 border-t border-slate-800 bg-slate-800/50">
          <div className="flex items-start gap-3 mb-4">
            <AlertCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <p className="text-sm text-slate-300 leading-relaxed">
              This will add demo commitments to your local ChronOS workspace. It simulates a hackathon environment with a compromised timeline and a watch-level task. It will overwrite any previous demo data.
            </p>
          </div>
          <div className="flex justify-end gap-3">
            <button
              onClick={() => setIsOpen(false)}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-black bg-amber-500 hover:bg-amber-400 rounded-lg transition-colors disabled:opacity-50"
            >
              {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
              Confirm Load Demo
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
