from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.db import models


def create_event(
    db: Session,
    raw_text: str,
    intent: str,
    extracted_json: Optional[Dict[str, Any]],
    confidence: float,
    status: str,
    sender: Optional[str],
    source: str,
    candidate_id: Optional[int] = None,
    action_summary: Optional[str] = None,
    error_message: Optional[str] = None,
) -> models.RecruitmentEvent:
    event = models.RecruitmentEvent(
        candidate_id=candidate_id,
        intent=intent,
        raw_text=raw_text,
        extracted_json=extracted_json,
        confidence=confidence,
        action_summary=action_summary,
        status=status,
        error_message=error_message,
        sender=sender,
        source=source,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(db: Session) -> List[models.RecruitmentEvent]:
    return db.query(models.RecruitmentEvent).order_by(models.RecruitmentEvent.created_at.desc()).all()
