export interface Candidate {
  id: number;
  name: string;
  phone?: string | null;
  email?: string | null;
  position_name?: string | null;
  source?: string | null;
  education?: string | null;
  school?: string | null;
  major?: string | null;
  graduation_year?: string | null;
  work_years?: string | null;
  skills?: string[] | null;
  experience_summary?: string | null;
  resume_summary?: string | null;
  resume_parse_status?: string | null;
  latest_resume_id?: number | null;
  match_score?: number | null;
  match_level?: string | null;
  stage: string;
  owner?: string | null;
  last_followup_at?: string | null;
  created_at: string;
  updated_at: string;
}
