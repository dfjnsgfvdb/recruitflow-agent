from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.db import models
from app.schemas.agent import AgentResult
from app.schemas.resume import ResumeParseResult
from app.services.candidate_service import find_candidate


def merge_resume_with_message(
    db: Session,
    message_agent_result: Optional[AgentResult],
    resume_parse_result: ResumeParseResult,
    position_name: Optional[str],
    sender: str,
    source: str,
) -> Tuple[models.Candidate, List[str], bool]:
    """合并 HR 消息和简历信息。HR 消息代表业务事实，简历代表履历事实，联系方式冲突需要人工复核。"""
    warnings = []
    need_review = False

    message_candidate = message_agent_result.candidate if message_agent_result else None
    resume_candidate = resume_parse_result.candidate

    message_phone = getattr(message_candidate, "phone", None) if message_candidate else None
    resume_phone = resume_candidate.phone
    message_email = getattr(message_candidate, "email", None) if message_candidate else None
    resume_email = resume_candidate.email

    if message_phone and resume_phone and message_phone != resume_phone:
        warnings.append("HR 消息手机号与简历手机号不一致，已保留原字段并标记 NEED_REVIEW")
        need_review = True
    if message_email and resume_email and message_email != resume_email:
        warnings.append("HR 消息邮箱与简历邮箱不一致，已保留原字段并标记 NEED_REVIEW")
        need_review = True

    final_name = _first_non_empty(
        getattr(message_candidate, "name", None) if message_candidate else None,
        resume_candidate.name,
        "未知候选人",
    )
    final_position_name = _first_non_empty(
        position_name,
        getattr(message_candidate, "position_name", None) if message_candidate else None,
    )
    final_phone = _first_non_empty(message_phone, resume_phone)
    final_email = _first_non_empty(message_email, resume_email)

    candidate = find_candidate(
        db,
        name=final_name,
        phone=final_phone,
        email=final_email,
        position_name=final_position_name,
    )
    now = datetime.now()

    if not candidate:
        candidate = models.Candidate(
            name=final_name,
            phone=final_phone,
            email=final_email,
            position_name=final_position_name,
            source=_first_non_empty(getattr(message_candidate, "source", None) if message_candidate else None, source),
            education=resume_candidate.education,
            school=resume_candidate.school,
            major=resume_candidate.major,
            graduation_year=resume_candidate.graduation_year,
            work_years=resume_candidate.work_years,
            skills=resume_parse_result.skills,
            experience_summary=_first_non_empty(
                getattr(message_candidate, "experience_summary", None) if message_candidate else None,
                resume_parse_result.resume_summary,
            ),
            resume_summary=resume_parse_result.resume_summary,
            resume_parse_status="NEED_REVIEW" if need_review or resume_parse_result.need_manual_review else "SUCCESS",
            stage=_infer_stage(message_agent_result),
            owner=sender,
            last_followup_at=now,
        )
        db.add(candidate)
    else:
        _fill_if_empty(candidate, "phone", final_phone)
        _fill_if_empty(candidate, "email", final_email)
        _fill_if_empty(candidate, "position_name", final_position_name)
        _fill_if_empty(candidate, "source", source)
        # 简历字段优先来自 PDF，因为它比 HR 备注更完整。
        _assign_if_value(candidate, "education", resume_candidate.education)
        _assign_if_value(candidate, "school", resume_candidate.school)
        _assign_if_value(candidate, "major", resume_candidate.major)
        _assign_if_value(candidate, "graduation_year", resume_candidate.graduation_year)
        _assign_if_value(candidate, "work_years", resume_candidate.work_years)
        if resume_parse_result.skills:
            candidate.skills = resume_parse_result.skills
        _assign_if_value(candidate, "resume_summary", resume_parse_result.resume_summary)
        _fill_if_empty(candidate, "experience_summary", resume_parse_result.resume_summary)
        candidate.resume_parse_status = "NEED_REVIEW" if need_review or resume_parse_result.need_manual_review else "SUCCESS"
        candidate.last_followup_at = now

    db.commit()
    db.refresh(candidate)
    return candidate, warnings, need_review


def _infer_stage(message_agent_result: Optional[AgentResult]) -> str:
    if not message_agent_result:
        return "NEW"
    if message_agent_result.stage_change and message_agent_result.stage_change.new_stage:
        return message_agent_result.stage_change.new_stage
    if message_agent_result.intent == "CREATE_CANDIDATE" and "简历通过" in str(message_agent_result):
        return "RESUME_PASSED"
    return "NEW"


def _first_non_empty(*values):
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _fill_if_empty(candidate: models.Candidate, field: str, value) -> None:
    if value and not getattr(candidate, field):
        setattr(candidate, field, value)


def _assign_if_value(candidate: models.Candidate, field: str, value) -> None:
    if value:
        setattr(candidate, field, value)
