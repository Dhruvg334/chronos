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
