export interface AgentMessageRequest {
  message: string;
  sender?: string;
  source?: string;
}

export interface AgentAction {
  tool: string;
  args: Record<string, unknown>;
  risk_level: string;
}

export interface AgentCandidateInfo {
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  position_name?: string | null;
  source?: string | null;
  education?: string | null;
  school?: string | null;
  experience_summary?: string | null;
  owner?: string | null;
}

export interface AgentStageChange {
  old_stage?: string | null;
  new_stage?: string | null;
  reason?: string | null;
}

export interface AgentInterviewInfo {
  round?: string | null;
  interview_time?: string | null;
  interviewer?: string | null;
  location?: string | null;
  result?: string | null;
  feedback?: string | null;
}

export interface AgentQueryInfo {
  position_name?: string | null;
  time_range?: string | null;
  metric?: string | null;
}

export interface AgentResult {
  intent: string;
  confidence: number;
  candidate: AgentCandidateInfo;
  stage_change: AgentStageChange;
  interview: AgentInterviewInfo;
  query: AgentQueryInfo;
  actions: AgentAction[];
  need_clarification: boolean;
  clarification_questions: string[];
}

export interface ToolExecutionResult {
  tool: string;
  success: boolean;
  status: string;
  message: string;
  data?: unknown;
  risk_level: string;
  need_confirmation: boolean;
  pending_action_id?: number | null;
  error_message?: string | null;
}

export interface AgentProcessResponse {
  success: boolean;
  need_clarification: boolean;
  message: string;
  agent_result: AgentResult;
  executed_actions: ToolExecutionResult[];
}
