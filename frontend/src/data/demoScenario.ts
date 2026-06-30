export type DemoRiskLevel = 'rescue_required' | 'at_risk' | 'watch' | 'stable';

export interface DemoCommitment {
  title: string;
  description: string;
  deadline: string;
  remainingMinutes: number;
  availableMinutes: number;
  risk: DemoRiskLevel;
  nextMove: string;
}

export interface DemoSuggestion {
  agent: 'Scheduling Agent' | 'Rescue Agent';
  title: string;
  commitment: string;
  reason: string;
  action: string;
}

export const demoCommitments: DemoCommitment[] = [
  {
    title: 'Final submission build',
    description: 'Finish the core demo, README, deployment checks, and product walkthrough before submission.',
    deadline: 'Tonight, 11:30 PM',
    remainingMinutes: 210,
    availableMinutes: 95,
    risk: 'rescue_required',
    nextMove: 'Approve one rescue block before adding new work.',
  },
  {
    title: 'Record demo video',
    description: 'Prepare a short walkthrough that shows brain dump, analysis, approval, and recovery.',
    deadline: 'Tomorrow morning',
    remainingMinutes: 60,
    availableMinutes: 95,
    risk: 'watch',
    nextMove: 'Keep this behind the submission build until the critical block is protected.',
  },
  {
    title: 'Technical interview prep',
    description: 'Review backend auth, LangGraph traces, and product architecture talking points.',
    deadline: 'This week',
    remainingMinutes: 120,
    availableMinutes: 180,
    risk: 'stable',
    nextMove: 'Schedule after the deadline recovery path is under control.',
  },
];

export const demoSuggestions: DemoSuggestion[] = [
  {
    agent: 'Rescue Agent',
    title: 'Protect a 90-minute rescue block',
    commitment: 'Final submission build',
    reason: 'Remaining effort is higher than available focus capacity before the deadline.',
    action: 'Create a focused recovery block and pause lower-priority work.',
  },
  {
    agent: 'Scheduling Agent',
    title: 'Move demo video after the rescue block',
    commitment: 'Record demo video',
    reason: 'The video matters, but it should not consume the next critical focus window.',
    action: 'Schedule it after the submission build is stabilized.',
  },
  {
    agent: 'Scheduling Agent',
    title: 'Keep interview prep in the safe zone',
    commitment: 'Technical interview prep',
    reason: 'This commitment is useful but not urgent today.',
    action: 'Leave it for a later stable block.',
  },
];

export const riskLabels: Record<DemoRiskLevel, string> = {
  rescue_required: 'Rescue required',
  at_risk: 'At risk',
  watch: 'Watch',
  stable: 'Stable',
};

export const riskClasses: Record<DemoRiskLevel, string> = {
  rescue_required: 'bg-risk-critical text-white',
  at_risk: 'bg-risk-atrisk text-white',
  watch: 'bg-warm-cream text-risk-watch border border-warm-border',
  stable: 'bg-green-50 text-risk-stable border border-green-100',
};
