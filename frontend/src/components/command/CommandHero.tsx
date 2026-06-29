import { Play, Activity } from 'lucide-react';
import { InfoHint } from '../ui/InfoHint';
import { HowChronOSWorks } from './HowChronOSWorks';

interface CommandHeroProps {
  onAnalyze: () => void;
  isAnalyzing: boolean;
  onLoadDemo: () => Promise<void>;
}

export function CommandHero({ onAnalyze, isAnalyzing, onLoadDemo }: CommandHeroProps) {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
      <div>
        <div className="flex items-center gap-4 mb-2">
          <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">ChronOS Command</h1>
          <HowChronOSWorks />
        </div>
        <p className="text-text-secondary">
          Secure AI Time Operating System. Drop your messy commitments here, and ChronOS will calmly help you recover control.
        </p>
      </div>
      <div className="flex gap-3">
        <button
          onClick={onLoadDemo}
          className="px-6 py-2.5 font-semibold text-text-secondary bg-white border border-warm-border rounded-lg hover:bg-warm-ivory hover:text-text-primary transition-colors shadow-sm"
        >
          Load Judge Demo
        </button>
        <button
          onClick={onAnalyze}
          disabled={isAnalyzing}
          className="relative inline-flex items-center justify-center gap-2 px-6 py-2.5 font-semibold text-white transition-all bg-accent-amber rounded-lg hover:bg-accent-terracotta focus:outline-none focus:ring-2 focus:ring-accent-amber/50 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
        >
          {isAnalyzing ? (
            <Activity className="w-5 h-5 animate-pulse" />
          ) : (
            <Play className="w-5 h-5 fill-current" />
          )}
          <span>{isAnalyzing ? 'Analyzing...' : 'Run ChronOS Analysis'}</span>
        </button>
        <div className="self-center">
          <InfoHint content="Refreshes your timeline, checks capacity, finds deadline risk, and prepares human-approved actions. It never creates focus blocks without your approval." />
        </div>
      </div>
    </div>
  );
}
