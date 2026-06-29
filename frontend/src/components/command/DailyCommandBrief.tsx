import { Activity, ShieldCheck, Clock, CheckCircle2, AlertTriangle } from 'lucide-react';
import { InfoHint } from '../ui/InfoHint';

export interface CommandBriefData {
  time_health: string;
  time_health_explanation: string;
  capacity_source: string;
  available_minutes_today: number;
  rescue_candidate_count: number;
  schedule_proposal_count: number;
  next_best_action: string;
}

interface DailyCommandBriefProps {
  brief: CommandBriefData | null;
}

export function DailyCommandBrief({ brief }: DailyCommandBriefProps) {
  if (!brief) return null;

  const getHealthIcon = () => {
    switch (brief.time_health) {
      case 'Stable': return <ShieldCheck className="w-6 h-6 text-risk-stable" />;
      case 'Watch': return <Activity className="w-6 h-6 text-risk-watch" />;
      case 'Compromised': return <AlertTriangle className="w-6 h-6 text-risk-atrisk" />;
      case 'Rescue Required': return <AlertTriangle className="w-6 h-6 text-risk-critical" />;
      default: return <Activity className="w-6 h-6 text-text-muted" />;
    }
  };

  const getHealthColor = () => {
    switch (brief.time_health) {
      case 'Stable': return 'text-risk-stable';
      case 'Watch': return 'text-risk-watch';
      case 'Compromised': return 'text-risk-atrisk';
      case 'Rescue Required': return 'text-risk-critical';
      default: return 'text-text-muted';
    }
  };

  return (
    <div className="bg-warm-cream border border-warm-border rounded-xl p-6 mb-8 shadow-sm">
      <div className="mb-6">
        <h2 className="text-xl font-extrabold text-text-primary">Today's Command Brief</h2>
        <p className="text-sm text-text-secondary">ChronOS checked your commitments against your available focus time.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-4 rounded-xl border border-warm-border">
          <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2 flex items-center">
            Time Health
            <InfoHint content="ChronOS compares your deadlines, remaining effort, and available focus time to estimate whether your plan is still executable." />
          </p>
          <div className="flex items-center gap-2 mb-1">
            {getHealthIcon()}
            <span className={`text-xl font-bold ${getHealthColor()}`}>
              {brief.time_health}
            </span>
          </div>
          <p className="text-xs text-text-secondary">{brief.time_health_explanation}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-warm-border">
          <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2 flex items-center">
            Focus Capacity
            <InfoHint content="Your estimated usable work time after calendar events and existing focus blocks." />
          </p>
          <div className="flex items-center gap-2 mb-1">
            <Clock className="w-6 h-6 text-blue-500" />
            <span className="text-xl font-bold text-text-primary">
              {brief.available_minutes_today} <span className="text-sm font-medium text-text-muted">mins</span>
            </span>
          </div>
          <p className="text-xs text-text-secondary">Source: {brief.capacity_source === 'google_calendar' ? 'Google Calendar' : 'Mock / Default'}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-warm-border">
          <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2 flex items-center">
            Pending Approvals
          </p>
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle2 className="w-6 h-6 text-purple-500" />
            <span className="text-xl font-bold text-text-primary">
              {brief.schedule_proposal_count} <span className="text-sm font-medium text-text-muted">actions</span>
            </span>
          </div>
          <p className="text-xs text-text-secondary">{brief.rescue_candidate_count > 0 ? `${brief.rescue_candidate_count} rescue candidates detected.` : 'No critical rescues needed.'}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-warm-border">
          <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2 flex items-center">
            Next Best Action
          </p>
          <div className="bg-warm-ivory p-3 rounded-lg border border-warm-border h-[52px] flex items-center">
            <p className="text-sm font-semibold text-accent-amber truncate">
              {brief.next_best_action}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
