import type { ToolExecutionResult } from './agent';

export interface PendingAction {
  id: number;
  candidate_id?: number | null;
  action_type: string;
  risk_level: string;
  payload?: Record<string, unknown> | null;
  reason?: string | null;
  status: string;
  requested_by?: string | null;
  approved_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConfirmationActionResponse {
  success: boolean;
  message: string;
  pending_action?: PendingAction | null;
  executed_result?: ToolExecutionResult | null;
}
