from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class CandidateOut(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    position_name: Optional[str] = None
    source: Optional[str] = None
    education: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[str] = None
    work_years: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_summary: Optional[str] = None
    resume_summary: Optional[str] = None
    resume_parse_status: Optional[str] = None
    latest_resume_id: Optional[int] = None
    match_score: Optional[float] = None
    match_level: Optional[str] = None
    stage: str
    owner: Optional[str] = None
    last_followup_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
