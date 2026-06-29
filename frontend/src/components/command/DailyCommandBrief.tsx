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
      case 'Stable': return <ShieldCheck className="w-6 h-6 text-[#3D663D]" />;
      case 'Watch': return <Activity className="w-6 h-6 text-[#B57C45]" />;
      case 'Compromised': return <AlertTriangle className="w-6 h-6 text-[#CC6633]" />;
      case 'Rescue Required': return <AlertTriangle className="w-6 h-6 text-[#993333]" />;
      default: return <Activity className="w-6 h-6 text-[#7A7771]" />;
    }
  };

  const getHealthColor = () => {
    switch (brief.time_health) {
      case 'Stable': return 'text-[#3D663D]';
      case 'Watch': return 'text-[#B57C45]';
      case 'Compromised': return 'text-[#CC6633]';
      case 'Rescue Required': return 'text-[#993333]';
      default: return 'text-[#7A7771]';
    }
  };

  return (
    <div className="bg-white border border-[#E5E0D8] rounded-2xl p-6 mb-8 shadow-sm">
      <div className="mb-6">
        <h2 className="text-xl font-extrabold text-[#2C2B29]">Today's Command Brief</h2>
        <p className="text-sm text-[#5C5A56]">ChronOS checked your commitments against your available focus time.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-[#FAF9F6] p-4 rounded-xl border border-[#E5E0D8]">
          <p className="text-xs font-semibold text-[#7A7771] uppercase tracking-wider mb-2 flex items-center">
            Time Health
            <InfoHint content="ChronOS compares your deadlines, remaining effort, and available focus time to estimate whether your plan is still executable." />
          </p>
          <div className="flex items-center gap-2 mb-1">
            {getHealthIcon()}
            <span className={`text-xl font-bold ${getHealthColor()}`}>
              {brief.time_health}
            </span>
          </div>
          <p className="text-xs text-[#5C5A56]">{brief.time_health_explanation}</p>
        </div>

        <div className="bg-[#FAF9F6] p-4 rounded-xl border border-[#E5E0D8]">
          <p className="text-xs font-semibold text-[#7A7771] uppercase tracking-wider mb-2 flex items-center">
            Focus Capacity
            <InfoHint content="Your estimated usable work time after calendar events and existing focus blocks." />
          </p>
          <div className="flex items-center gap-2 mb-1">
            <Clock className="w-6 h-6 text-[#4A90E2]" />
            <span className="text-xl font-bold text-[#2C2B29]">
              {brief.available_minutes_today} <span className="text-sm font-medium text-[#7A7771]">mins</span>
            </span>
          </div>
          <p className="text-xs text-[#5C5A56]">Source: {brief.capacity_source === 'google_calendar' ? 'Google Calendar' : 'Mock / Default'}</p>
        </div>

        <div className="bg-[#FAF9F6] p-4 rounded-xl border border-[#E5E0D8]">
          <p className="text-xs font-semibold text-[#7A7771] uppercase tracking-wider mb-2 flex items-center">
            Pending Approvals
          </p>
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle2 className="w-6 h-6 text-[#8B5CF6]" />
            <span className="text-xl font-bold text-[#2C2B29]">
              {brief.schedule_proposal_count} <span className="text-sm font-medium text-[#7A7771]">actions</span>
            </span>
          </div>
          <p className="text-xs text-[#5C5A56]">{brief.rescue_candidate_count > 0 ? `${brief.rescue_candidate_count} rescue candidates detected.` : 'No critical rescues needed.'}</p>
        </div>

        <div className="bg-[#FAF9F6] p-4 rounded-xl border border-[#E5E0D8]">
          <p className="text-xs font-semibold text-[#7A7771] uppercase tracking-wider mb-2 flex items-center">
            Next Best Action
          </p>
          <div className="bg-white p-3 rounded-lg border border-[#E5E0D8] h-[52px] flex items-center">
            <p className="text-sm font-semibold text-[#B57C45] truncate">
              {brief.next_best_action}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
