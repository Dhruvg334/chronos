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
    <div className="mt-6 border border-warm-border rounded-xl overflow-hidden bg-white shadow-sm">
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-warm-ivory rounded-lg border border-warm-border">
            <Database className="w-4 h-4 text-text-muted" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text-primary">Sample Scenario</h3>
            <p className="text-xs text-text-secondary">Load a realistic last-minute recovery case.</p>
          </div>
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="px-3 py-1.5 text-xs font-semibold text-text-secondary bg-warm-ivory border border-warm-border hover:bg-warm-border rounded-lg transition-colors"
        >
          Load sample
        </button>
      </div>

      {isOpen && (
        <div className="p-4 border-t border-warm-border bg-warm-ivory">
          <div className="flex items-start gap-2 mb-4">
            <AlertCircle className="w-4 h-4 text-accent-terracotta shrink-0 mt-0.5" />
            <p className="text-xs text-text-secondary leading-relaxed font-medium">
              This adds a sample deadline-recovery scenario to your ChronOS workspace and replaces any previous demo data.
            </p>
          </div>
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setIsOpen(false)}
              disabled={isLoading}
              className="px-3 py-1.5 text-xs font-semibold text-text-muted hover:text-text-primary transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={isLoading}
              className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-white bg-accent-amber hover:bg-accent-terracotta rounded-lg transition-colors disabled:opacity-50"
            >
              {isLoading && <Loader2 className="w-3 h-3 animate-spin" />}
              Confirm Load sample
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
