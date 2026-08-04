export interface BrainDumpRequest {
  text: string;
}

export interface ClarifyingQuestion {
  question: string;
  context?: string | null;
  field: string;
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
  kind?: 'event' | 'task' | 'routine' | 'project_outcome' | 'dependency';
  source_text?: string | null;
  deadline_precision?: 'exact' | 'window' | 'ambiguous' | 'none';
  effort_confidence?: 'known' | 'approximate' | 'unknown';
  dependencies?: string[];
  project_id?: string | null;
  outcome_id?: string | null;
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
  next_action: { commitment_id: string; task_id?: string | null; title: string; detail: string; estimated_minutes: number; project?: { id: string; title: string } | null; outcome?: { id: string; title: string } | null } | null;
  ordered_plan: PlanItem[];
  attention_count: number;
  strategy_recommendation: StrategyRecommendation | null;
  pending_approval_count: number;
  active_focus_session: ActiveFocusSession | null;
  recovery: RecoverySummary | null;
  explanation?: PlanExplanation | null;
  routines_due?: Array<{ id: string; title: string; preferred_time?: string | null; duration_minutes: number; minimum_viable_version: string }>;
  focus_duration_options: number[];
  explanation_detail: 'brief' | 'standard' | 'detailed';
}

export interface RecoveryOption { id: string; title: string; rationale: string; tradeoff: string; expected_impact: string; feasible: boolean; requires_approval: true }
export interface RecoverySummary { recommendation_key: string; commitment_id: string; title: string; what_changed: string; failure_mode: string; reason: string; options: RecoveryOption[]; recommended_option_id: string; requires_approval: true }
export interface StuckOption { id: string; title: string; rationale: string; duration_minutes?: number; commitment_id?: string; requires_approval: boolean }

export interface ProjectSummary { id: string; title: string; description: string; status: 'active' | 'paused' | 'completed' | 'archived'; target_date?: string | null; colour: string; outcome_count: number; completed_outcome_count: number; progress_percent: number; next_action?: string | null }
export interface Outcome { id: string; project_id?: string | null; title: string; description: string; status: 'active' | 'blocked' | 'uncertain' | 'completed' | 'archived'; target_date?: string | null; importance: number; estimated_effort_minutes?: number | null; confidence: number; completion_criteria: string; provenance?: string | null }
export interface ProjectDetail extends ProjectSummary { outcomes: Outcome[]; linked_commitments: SavedCommitment[]; available_commitments: SavedCommitment[] }
export interface Routine { id: string; title: string; frequency_rule: 'daily' | 'weekly'; preferred_days: number[]; preferred_time?: string | null; minimum_viable_version: string; estimated_duration_minutes: number; active: boolean; continuity_recovery?: string | null; occurrences: Array<{ date: string; status: string; preferred_time?: string | null }> }
export interface WeeklyDayCapacity { date: string; available_minutes: number; scheduled_minutes: number; remaining_minutes: number; buffer_minutes: number; over_capacity_minutes: number; confidence: string; sources: string[] }
export interface WeeklyView { week_start: string; timezone: string; days: WeeklyDayCapacity[]; due_outcomes: Outcome[]; unscheduled_work: SavedCommitment[]; routine_occurrences: Array<{ routine_id: string; title: string; occurrences: Array<{ date: string; status: string }>; continuity_recovery?: string | null }>; active_projects: ProjectSummary[]; primary_strategy?: StrategyRecommendation | null }
export interface WeeklyProposal { id: string; status: 'pending' | 'approved' | 'rejected'; week_start: string; focus_set: Array<{ id: string; title: string; project_title?: string | null }>; blocks: Array<{ commitment_id: string; title: string; start_at: string; duration_minutes: number; outcome_id?: string | null; project_id?: string | null }>; deferred: Array<{ id: string; title: string; reason: string }>; explanation: { constraints_considered: string[]; summary: string; ai_used: boolean; requires_approval: boolean }; requires_approval: boolean }

export interface PlanExplanation {
  detail?: 'brief' | 'standard' | 'detailed';
  constraints_considered: string[];
  next_action_reason: string;
  deferred: string[];
  changed: string;
  ai_used: boolean;
  requires_approval: boolean;
  sources?: ContextCitation[];
  retrieval_available?: boolean;
}

export interface ContextCitation { source_id: string; source_title: string; source_type: string; excerpt: string; reason_selected: string; confidence: 'low' | 'medium' | 'high'; retrieval_method: 'hybrid' | 'memory' | 'structured' | 'history'; score: number }
export interface MemoryItem { id: string; project_id?: string | null; category: 'preference' | 'constraint' | 'working_pattern' | 'project_fact' | 'personal_rule' | 'decision'; content: string; source_type: string; source_reference: { label?: string; correction_history?: Array<{ content: string; corrected_at: string }> }; confidence: number; is_explicit: boolean; status: 'proposed' | 'confirmed' | 'rejected' | 'archived' | 'expired'; effective_date?: string | null; review_at?: string | null; expires_at?: string | null; conflicts?: Array<{ id: string; content: string; message: string }> }
export interface KnowledgeSource { id: string; project_id?: string | null; source_type: 'note' | 'document' | 'pasted_text' | 'project_context'; title: string; status: 'processing' | 'ready' | 'failed' | 'archived'; original_metadata: Record<string, unknown>; checksum: string; failure_code?: string | null; created_at?: string }

export interface AdaptivePlanResponse {
  workflow_id: string;
  proposal_id: string;
  recommended_plan: {
    label: string;
    summary: string;
    feasibility: 'valid';
    blocks: Array<{ commitment_id: string; start_at: string; duration_minutes: number; rationale: string }>;
    deferred_commitment_ids: string[];
  };
  explanation: PlanExplanation;
  rejected_candidate_count: number;
  requires_approval: true;
}

export interface PlanResponse {
  timezone?: string;
  range_start: string;
  range_end: string;
  calendar_events: PlanItem[];
  plan_blocks: PlanItem[];
  unscheduled_commitments: PlanItem[];
  ordered_timeline: PlanItem[];
  capacity: { total_minutes: number; busy_minutes: number; planned_minutes: number; buffer_minutes: number; available_minutes: number; total_available_minutes: number; scheduled_minutes: number; remaining_minutes: number; over_capacity_minutes: number; confidence: 'low' | 'medium' | 'high'; sources: string[]; calendar_state: string; last_successful_sync?: string | null; retry_available?: boolean };
  buffer_guidance: string;
  explanation?: PlanExplanation | null;
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
  onboarding_status: 'not_started' | 'in_progress' | 'completed' | 'skipped';
  onboarding_step: number;
  onboarding_completed_at?: string | null;
  planning_style: 'guided' | 'balanced' | 'minimal';
  recommendation_frequency: 'low' | 'normal' | 'high';
  approval_strictness: 'always_ask' | 'allow_reversible';
  internal_write_automation_enabled: boolean;
  preferred_focus_durations: number[];
  routine_continuity_preference: 'gentle' | 'standard' | 'structured';
  quick_task_mode: 'immediate' | 'batch';
  strategy_preferences: string[];
  explanation_detail: 'brief' | 'standard' | 'detailed';
  updated_at?: string | null;
}

export type PersonalPreferences = Pick<PlanningProfile, 'planning_style' | 'recommendation_frequency' | 'approval_strictness' | 'internal_write_automation_enabled' | 'preferred_focus_durations' | 'routine_continuity_preference' | 'quick_task_mode' | 'strategy_preferences' | 'explanation_detail'>;

export interface IntegrationStatus {
  provider: string;
  access: 'read_only';
  state: 'connected' | 'disconnected' | 'unavailable' | 'configuration_missing';
  last_successful_sync: string | null;
  retry_available: boolean;
  planning_mode: 'calendar_and_profile' | 'profile_only';
  message: string;
}
