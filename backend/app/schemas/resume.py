from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ResumeCandidateInfo(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    education: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[str] = None
    work_years: Optional[str] = None


class ResumeParseResult(BaseModel):
    candidate: ResumeCandidateInfo = Field(default_factory=ResumeCandidateInfo)
    skills: List[str] = Field(default_factory=list)
    project_experiences: List[Dict[str, Any]] = Field(default_factory=list)
    work_experiences: List[Dict[str, Any]] = Field(default_factory=list)
    certificates: List[str] = Field(default_factory=list)
    resume_summary: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    suggested_interview_questions: List[str] = Field(default_factory=list)
    confidence: float = 0
    need_manual_review: bool = False
    warnings: List[str] = Field(default_factory=list)


class ResumeFileOut(BaseModel):
    id: int
    candidate_id: Optional[int] = None
    original_filename: str
    stored_filename: str
    file_path: str
    file_hash: str
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    parse_status: str
    raw_text: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None
    resume_summary: Optional[str] = None
    skill_tags: Optional[List[str]] = None
    confidence: float = 0
    error_message: Optional[str] = None
    uploaded_by: Optional[str] = None
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeScreeningReportOut(BaseModel):
    id: int
    candidate_id: int
    resume_file_id: int
    position_name: Optional[str] = None
    job_requirements: Optional[str] = None
    match_score: float = 0
    match_level: Optional[str] = None
    match_reason: Optional[str] = None
    strengths: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    missing_requirements: Optional[List[str]] = None
    suggested_interview_questions: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeUploadResponse(BaseModel):
    success: bool
    message: str
    candidate: Optional[Dict[str, Any]] = None
    resume_file: Optional[Dict[str, Any]] = None
    resume_parse_result: Optional[Dict[str, Any]] = None
    screening_report: Optional[Dict[str, Any]] = None
    warnings: List[str] = Field(default_factory=list)


class ResumeScreenRequest(BaseModel):
    position_name: str
    job_requirements: Optional[str] = None
