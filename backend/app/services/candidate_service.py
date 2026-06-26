from datetime import datetime
from typing import List, Optional, Union

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db import models
from app.schemas.agent import AgentCandidateInfo


def _candidate_value(candidate_info: Union[AgentCandidateInfo, dict], field: str):
    if isinstance(candidate_info, dict):
        return candidate_info.get(field)
    return getattr(candidate_info, field, None)


def find_candidate(
    db: Session,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    position_name: Optional[str] = None,
) -> Optional[models.Candidate]:
    # 候选人去重优先级：手机号 > 邮箱 > 姓名 + 岗位。
    if phone:
        candidate = db.query(models.Candidate).filter(models.Candidate.phone == phone).first()
        if candidate:
            return candidate

    if email:
        candidate = db.query(models.Candidate).filter(models.Candidate.email == email).first()
        if candidate:
            return candidate

    if name and position_name:
        return (
            db.query(models.Candidate)
            .filter(and_(models.Candidate.name == name, models.Candidate.position_name == position_name))
            .first()
        )

    if name:
        return db.query(models.Candidate).filter(models.Candidate.name == name).first()

    return None


def create_or_update_candidate(
    db: Session,
    candidate_info: Union[AgentCandidateInfo, dict],
    stage: Optional[str] = None,
) -> models.Candidate:
    name = _candidate_value(candidate_info, "name") or "未知候选人"
    phone = _candidate_value(candidate_info, "phone")
    email = _candidate_value(candidate_info, "email")
    position_name = _candidate_value(candidate_info, "position_name")

    candidate = find_candidate(db, name=name, phone=phone, email=email, position_name=position_name)
    now = datetime.now()
    fields = [
        "phone",
        "email",
        "position_name",
        "source",
        "education",
        "school",
        "experience_summary",
        "owner",
    ]

    if candidate:
        # 已存在候选人时只补齐空字段，避免覆盖 HR 已维护的信息。
        for field in fields:
            value = _candidate_value(candidate_info, field)
            if value and not getattr(candidate, field):
                setattr(candidate, field, value)
        if stage:
            candidate.stage = stage
        candidate.last_followup_at = now
    else:
        candidate = models.Candidate(
            name=name,
            phone=phone,
            email=email,
            position_name=position_name,
            source=_candidate_value(candidate_info, "source"),
            education=_candidate_value(candidate_info, "education"),
            school=_candidate_value(candidate_info, "school"),
            experience_summary=_candidate_value(candidate_info, "experience_summary"),
            stage=stage or "NEW",
            owner=_candidate_value(candidate_info, "owner"),
            last_followup_at=now,
        )
        db.add(candidate)

    db.commit()
    db.refresh(candidate)
    return candidate


def list_candidates(db: Session) -> List[models.Candidate]:
    return db.query(models.Candidate).order_by(models.Candidate.created_at.desc()).all()
