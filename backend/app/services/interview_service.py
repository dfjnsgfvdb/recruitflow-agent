from datetime import datetime
from typing import List, Optional, Union

from sqlalchemy.orm import Session

from app.db import models
from app.schemas.agent import AgentInterviewInfo


def _parse_interview_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    candidates = [value, value.replace("/", "-")]
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
    for item in candidates:
        for fmt in formats:
            try:
                return datetime.strptime(item.strip(), fmt)
            except ValueError:
                continue
    return None


def create_interview(db: Session, candidate_id: int, interview_info: Union[AgentInterviewInfo, dict]) -> models.Interview:
    getter = interview_info.get if isinstance(interview_info, dict) else lambda key, default=None: getattr(interview_info, key, default)
    interview = models.Interview(
        candidate_id=candidate_id,
        round=getter("round"),
        interview_time=_parse_interview_time(getter("interview_time")),
        interviewer=getter("interviewer"),
        location=getter("location"),
        result=getter("result") or "PENDING",
        feedback=getter("feedback"),
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


def list_interviews(db: Session) -> List[models.Interview]:
    return db.query(models.Interview).order_by(models.Interview.created_at.desc()).all()
