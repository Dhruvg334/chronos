export interface BrainDumpRequest {
  text: string;
}

export interface ClarifyingQuestion {
  question: string;
  context?: string | null;
}

export interface ExtractedTask {
  title: string;
  estimated_minutes?: number | null;
}

export interface ExtractedCommitment {
  title: string;
  type: string;
  estimated_minutes?: number | null;
  deadline_at?: string | null; // ISO datetime string
  start_before_at?: string | null; // ISO datetime string
  importance: number;
  flexibility: number;
  done_condition?: string | null;
  next_action?: string | null;
  tasks: ExtractedTask[];
  missing_fields: string[];
  confidence_score: number;
}

export interface IntakeResponse {
  agent_run_id: string;
  drafts: ExtractedCommitment[];
  questions: ClarifyingQuestion[];
}

export type CommitmentDraft = ExtractedCommitment;

export interface ApproveCommitmentsRequest {
  agent_run_id: string;
  approved_drafts: ExtractedCommitment[];
}

export interface ApproveCommitmentsResponse {
  status: string;
  count: number;
  message: string;
}

// Trace event types for Agent Console
export interface AgentTraceEvent {
  id: string;
  agent_run_id: string;
  event_type: string;
  payload_json: any;
  created_at: string;
}
