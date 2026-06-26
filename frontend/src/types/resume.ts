export interface ResumeFile {
  id: number;
  candidate_id?: number | null;
  original_filename: string;
  parse_status: string;
  resume_summary?: string | null;
  skill_tags?: string[] | null;
  confidence: number;
  error_message?: string | null;
  uploaded_by?: string | null;
  source: string;
  created_at: string;
  updated_at: string;
  parsed_json?: Record<string, unknown> | null;
  raw_text?: string | null;
}

export interface ResumeScreeningReport {
  id: number;
  candidate_id: number;
  resume_file_id: number;
  position_name?: string | null;
  match_score: number;
  match_level?: string | null;
  match_reason?: string | null;
  strengths?: string[] | null;
  risks?: string[] | null;
  missing_requirements?: string[] | null;
  suggested_interview_questions?: string[] | null;
  created_at: string;
}

export interface ResumeParseCandidateInfo {
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  education?: string | null;
  school?: string | null;
  major?: string | null;
  graduation_year?: string | null;
  work_years?: string | null;
}

export interface ResumeParseResult {
  candidate: ResumeParseCandidateInfo;
  skills: string[];
  project_experiences: Array<Record<string, unknown>>;
  work_experiences: Array<Record<string, unknown>>;
  certificates: string[];
  resume_summary?: string | null;
  strengths: string[];
  risks: string[];
  suggested_interview_questions: string[];
  confidence: number;
  need_manual_review: boolean;
  warnings: string[];
}

export interface ResumeUploadCandidate {
  id?: number;
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  position_name?: string | null;
  education?: string | null;
  school?: string | null;
  major?: string | null;
  graduation_year?: string | null;
  work_years?: string | null;
  skills?: string[] | null;
  resume_summary?: string | null;
  resume_parse_status?: string | null;
  latest_resume_id?: number | null;
  match_score?: number | null;
  match_level?: string | null;
  stage?: string | null;
  source?: string | null;
}

export interface ResumeUploadResponse {
  success: boolean;
  message: string;
  candidate?: ResumeUploadCandidate | null;
  resume_file?: ResumeFile | null;
  resume_parse_result?: ResumeParseResult | null;
  screening_report?: ResumeScreeningReport | null;
  warnings: string[];
}

export interface ResumeScreenRequest {
  position_name: string;
  job_requirements?: string;
}

export interface CandidateResumeResponse {
  resume_file: ResumeFile;
  screening_report?: ResumeScreeningReport | null;
}
