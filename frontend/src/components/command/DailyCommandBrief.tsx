import { Activity, AlertTriangle, ShieldCheck, Clock, CheckCircle2 } from 'lucide-react';

export interface CommandBriefData {
  time_health: string;
  time_health_explanation: string;
  capacity_source: string;
  available_minutes_today: number;
  rescue_candidate_count: number;
  schedule_proposal_count: number;
  rescue_proposal_count?: number;
  pending_approval_count?: number;
  estimated_minutes_due_soon?: number;
  top_risk_title?: string | null;
  warnings?: string[];
  next_best_action: string;
}

interface DailyCommandBriefProps {
  brief: CommandBriefData | null;
}

export function DailyCommandBrief({ brief }: DailyCommandBriefProps) {
  if (!brief) return null;

  const getHealthIcon = () => {
    switch (brief.time_health) {
      case 'Stable': return <ShieldCheck className="w-6 h-6 text-emerald-500" />;
      case 'Watch': return <Activity className="w-6 h-6 text-amber-500" />;
      case 'Compromised': return <AlertTriangle className="w-6 h-6 text-orange-500" />;
      case 'Rescue Required': return <AlertTriangle className="w-6 h-6 text-rose-500 animate-pulse" />;
      default: return <Activity className="w-6 h-6 text-slate-400" />;
    }
  };

  const getHealthColor = () => {
    switch (brief.time_health) {
      case 'Stable': return 'text-emerald-500';
      case 'Watch': return 'text-amber-500';
      case 'Compromised': return 'text-orange-500';
      case 'Rescue Required': return 'text-rose-500';
      default: return 'text-slate-400';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8 shadow-lg shadow-black/20">
      <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
        <Activity className="w-5 h-5 text-amber-500" />
        Daily Command Brief
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="space-y-2">
          <p className="text-sm text-slate-400 font-medium">Time Health</p>
          <div className="flex items-center gap-3">
            {getHealthIcon()}
            <span className={`text-xl font-bold ${getHealthColor()}`}>
              {brief.time_health}
            </span>
          </div>
          <p className="text-xs text-slate-500">{brief.time_health_explanation}</p>
        </div>

        <div className="space-y-2">
          <p className="text-sm text-slate-400 font-medium">Today's Focus Capacity</p>
          <div className="flex items-center gap-3">
            <Clock className="w-6 h-6 text-blue-400" />
            <span className="text-xl font-bold text-white">
              {brief.available_minutes_today} <span className="text-sm font-normal text-slate-400">minutes</span>
            </span>
          </div>
          <p className="text-xs text-slate-500">Source: {brief.capacity_source === 'google_calendar' ? 'Google Calendar' : 'Mock / Default'}</p>
        </div>

        <div className="space-y-2">
          <p className="text-sm text-slate-400 font-medium">Pending Approvals</p>
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-6 h-6 text-purple-400" />
            <span className="text-xl font-bold text-white">
              {brief.pending_approval_count ?? brief.schedule_proposal_count} <span className="text-sm font-normal text-slate-400">actions</span>
            </span>
          </div>
          <p className="text-xs text-slate-500">{brief.rescue_candidate_count > 0 ? `${brief.rescue_candidate_count} rescue candidates detected.` : 'No critical rescues needed.'}</p>
        </div>

        <div className="space-y-2">
          <p className="text-sm text-slate-400 font-medium">Next Best Action</p>
          <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700">
            <p className="text-sm font-medium text-amber-400">
              {brief.next_best_action}
            </p>
          </div>
        </div>
      </div>

      {(brief.top_risk_title || brief.estimated_minutes_due_soon || (brief.warnings && brief.warnings.length > 0)) && (
        <div className="mt-6 pt-5 border-t border-slate-800 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-slate-500 text-xs uppercase tracking-wider font-bold mb-1">Top Risk</p>
            <p className="text-slate-300">{brief.top_risk_title || 'No active risk surfaced.'}</p>
          </div>
          <div>
            <p className="text-slate-500 text-xs uppercase tracking-wider font-bold mb-1">Due Soon Load</p>
            <p className="text-slate-300">{brief.estimated_minutes_due_soon ?? 0} minutes in the next 24h</p>
          </div>
          <div>
            <p className="text-slate-500 text-xs uppercase tracking-wider font-bold mb-1">Analysis Warnings</p>
            <p className="text-slate-300">{brief.warnings && brief.warnings.length > 0 ? brief.warnings[0] : 'None'}</p>
          </div>
        </div>
      )}
    </div>
  );
}
