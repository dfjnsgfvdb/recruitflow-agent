from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class InterviewOut(BaseModel):
    id: int
    candidate_id: int
    round: Optional[str] = None
    interview_time: Optional[datetime] = None
    interviewer: Optional[str] = None
    location: Optional[str] = None
    result: str
    feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
