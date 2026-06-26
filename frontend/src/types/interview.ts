export interface Interview {
  id: number;
  candidate_id: number;
  round?: string | null;
  interview_time?: string | null;
  interviewer?: string | null;
  location?: string | null;
  result: string;
  feedback?: string | null;
  created_at: string;
  updated_at: string;
}
