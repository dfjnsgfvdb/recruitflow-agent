export interface RecruitmentEvent {
  id: number;
  candidate_id?: number | null;
  intent: string;
  raw_text: string;
  extracted_json?: Record<string, unknown> | null;
  confidence: number;
  action_summary?: string | null;
  status: string;
  error_message?: string | null;
  sender?: string | null;
  source: string;
  created_at: string;
}
