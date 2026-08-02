export interface BrainDumpRequest {
  text: string;
}

export interface ClarifyingQuestion {
  question: string;
  context?: string | null;
}

export interface ExtractedTask {
  title: string;
  next_action?: string | null;
  done_condition?: string | null;
  estimated_minutes?: number | null;
  sequence_order?: number | null;
}

export interface ExtractedCommitment {
  title: string;
  description?: string | null;
  type: string;
  estimated_minutes?: number | null;
  deadline_at?: string | null;
  start_before_at?: string | null;
  importance: number;
  flexibility: number;
  progress_percent?: number | null;
  done_condition?: string | null;
  next_action?: string | null;
  tasks: ExtractedTask[];
  missing_fields: string[];
  confidence_score: number;
}

export type CommitmentDraft = ExtractedCommitment;

export interface IntakeResponse {
  agent_run_id: string;
  drafts: CommitmentDraft[];
  questions: ClarifyingQuestion[];
}

export interface ApproveCommitmentsRequest {
  agent_run_id: string;
  approved_drafts: CommitmentDraft[];
}

export interface ApproveCommitmentsResponse {
  status: string;
  count: number;
  message: string;
}

export interface AgentTraceEvent {
  id: string;
  agent_run_id: string;
  user_id?: string;
  step_name: string;
  tool_name?: string | null;
  status: 'started' | 'succeeded' | 'failed' | string;
  explanation: string;
  payload_json?: Record<string, unknown> | null;
  created_at: string;
}

export interface TimeSpineCheckpoint {
  id: string;
  status: 'completed' | 'pending' | string;
  label: string;
}

export interface TimeSpine {
  id: string;
  commitment_id: string;
  user_id: string;
  spine_json: TimeSpineCheckpoint[];
  current_stage: string;
  created_at?: string;
  updated_at?: string;
}

export interface SavedCommitment {
  id: string;
  user_id: string;
  title: string;
  description?: string | null;
  type: string;
  status: string;
  deadline_at?: string | null;
  start_before_at?: string | null;
  estimated_minutes: number;
  actual_minutes: number;
  importance: number;
  consequence?: string | null;
  flexibility: number;
  progress_percent: number;
  risk_level: string;
  risk_score: number;
  confidence_score: number;
  created_at?: string;
  updated_at?: string;
  time_spines?: TimeSpine[];
}

export interface TaskSchema {
  id: string;
  title: string;
  status: string;
  estimated_minutes: number;
  actual_minutes: number;
  sequence_order: number;
  next_action?: string | null;
  done_condition?: string | null;
}

export interface FocusBlockSchema {
  id: string;
  title: string;
  start_at: string;
  end_at: string;
  block_type: string;
  status: string;
}

export interface ReflectionSchema {
  id: string;
  planned_minutes: number;
  actual_minutes: number;
  completion_status: string;
  energy_level: number;
  blocker_reason?: string | null;
  quality_confidence?: string | null;
  notes?: string | null;
}

export interface NormalizedTimeSpineStage {
  key: string;
  label: string;
  order: number;
  status: string;
  timestamp?: string | null;
  risk_level?: string | null;
  explanation?: string | null;
}

export interface CommitmentDetailResponse extends SavedCommitment {
  tasks: TaskSchema[];
  time_spine_stages: NormalizedTimeSpineStage[];
  focus_blocks: FocusBlockSchema[];
  reflections: ReflectionSchema[];
  current_stage?: string | null;
}

export interface GoogleConnectionStatus {
  connected: boolean;
  email?: string;
  scopes?: string[];
  last_synced_at?: string;
}

export interface CapacityAvailability {
  capacity_source: "google_calendar" | "mock";
  available_minutes: number;
  focus_windows: any[];
  busy_blocks_count: number;
  fallback_reason?: string;
}

export interface StrategyRecommendation {
  strategy: string;
  title: string;
  why: string;
  evidence: string[];
  action: string;
  tradeoff: string;
  automatic_change: false;
  confidence: 'low' | 'medium' | 'high';
  alternatives: string[];
}

export interface PlanItem {
  id: string;
  kind: 'calendar_event' | 'focus_block' | 'commitment';
  title: string;
  start_at?: string | null;
  end_at?: string | null;
  commitment_id?: string | null;
  status: string;
}

export interface ActiveFocusSession {
  id: string;
  commitment_id: string;
  title: string;
  status: 'active' | 'paused';
  planned_minutes: number;
  elapsed_seconds: number;
  remaining_seconds: number;
  started_at: string;
  paused_at?: string | null;
}

export interface TodayResponse {
  status: 'clear' | 'attention' | 'empty';
  status_message: string;
  next_action: { commitment_id: string; task_id?: string | null; title: string; detail: string; estimated_minutes: number } | null;
  ordered_plan: PlanItem[];
  attention_count: number;
  strategy_recommendation: StrategyRecommendation | null;
  pending_approval_count: number;
  active_focus_session: ActiveFocusSession | null;
  recovery: { commitment_id: string; title: string; reason: string; options: string[]; requires_approval: true } | null;
}

export interface PlanResponse {
  timezone?: string;
  range_start: string;
  range_end: string;
  calendar_events: PlanItem[];
  plan_blocks: PlanItem[];
  unscheduled_commitments: PlanItem[];
  ordered_timeline: PlanItem[];
  capacity: { total_minutes: number; busy_minutes: number; planned_minutes: number; buffer_minutes: number; available_minutes: number; total_available_minutes: number; scheduled_minutes: number; remaining_minutes: number; over_capacity_minutes: number; confidence: 'low' | 'medium' | 'high'; sources: string[]; calendar_state: string };
  buffer_guidance: string;
}

export interface PlanningProfile {
  timezone: string;
  available_weekdays: number[];
  working_start_time: string;
  working_end_time: string;
  daily_focus_limit_minutes: number;
  default_focus_duration_minutes: number;
  minimum_transition_buffer_minutes: number;
  minimum_daily_unscheduled_buffer_minutes: number;
  protected_interval_start: string | null;
  protected_interval_end: string | null;
  quick_task_threshold_minutes: number;
  updated_at?: string | null;
}

export interface IntegrationStatus {
  provider: string;
  access: 'read_only';
  state: 'connected' | 'disconnected' | 'unavailable' | 'configuration_missing';
  last_successful_sync: string | null;
  retry_available: boolean;
  planning_mode: 'calendar_and_profile' | 'profile_only';
  message: string;
}
