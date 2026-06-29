import { Activity, Play } from 'lucide-react';
import { HowChronOSWorks } from './HowChronOSWorks';

interface CommandHeroProps {
  onAnalyze: () => void;
  isAnalyzing: boolean;
}

export function CommandHero({ onAnalyze, isAnalyzing }: CommandHeroProps) {
  return (
    <section className="mb-8">
      <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
        <div className="max-w-xl">
          <div className="mb-2 flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">ChronOS Command</h1>
            <HowChronOSWorks />
          </div>
          <p className="text-base leading-7 text-text-secondary">
            Drop your messy commitments here. ChronOS checks what is slipping, what can wait,
            and what needs your approval next.
          </p>
        </div>

        <div className="shrink-0 md:pt-1">
          <button
            onClick={onAnalyze}
            disabled={isAnalyzing}
            title="Refreshes your timeline, checks capacity, finds deadline risk, and prepares human-approved actions. It never creates focus blocks without your approval."
            className="inline-flex min-w-[230px] items-center justify-center gap-2 rounded-xl bg-accent-amber px-7 py-3 text-sm font-bold text-white shadow-sm transition-all hover:bg-accent-terracotta focus:outline-none focus:ring-2 focus:ring-accent-amber/40 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isAnalyzing ? (
              <Activity className="h-4 w-4 animate-pulse" />
            ) : (
              <Play className="h-4 w-4 fill-current" />
            )}
            <span className="whitespace-nowrap">{isAnalyzing ? 'Analyzing your plan…' : 'Run ChronOS Analysis'}</span>
          </button>
          <p className="mt-2 max-w-[230px] text-center text-xs leading-5 text-text-muted">
            Checks risk and prepares suggestions. Nothing runs without approval.
          </p>
        </div>
      </div>
    </section>
  );
}
