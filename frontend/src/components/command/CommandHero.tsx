import { Play, Activity } from 'lucide-react';

interface CommandHeroProps {
  onAnalyze: () => void;
  isAnalyzing: boolean;
}

export function CommandHero({ onAnalyze, isAnalyzing }: CommandHeroProps) {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4 bg-slate-900/50 p-6 rounded-xl border border-slate-800/50 backdrop-blur-sm">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">ChronOS Command Center</h1>
        <p className="text-slate-400">
          Secure AI Time Operating System. Predicts deadline collapse and proposes human-approved rescue actions.
        </p>
      </div>
      <button
        onClick={onAnalyze}
        disabled={isAnalyzing}
        className="group relative inline-flex items-center justify-center gap-2 px-6 py-3 font-semibold text-white transition-all bg-amber-500 rounded-lg hover:bg-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden"
      >
        <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform ease-out duration-300" />
        {isAnalyzing ? (
          <Activity className="w-5 h-5 animate-pulse" />
        ) : (
          <Play className="w-5 h-5 fill-current" />
        )}
        <span className="relative">{isAnalyzing ? 'Analyzing...' : 'Run ChronOS Analysis'}</span>
      </button>
    </div>
  );
}
