from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.db import models

TERMINAL_STAGES = {"HIRED", "REJECTED", "RESUME_REJECTED", "FIRST_INTERVIEW_REJECTED"}


def _hours_between(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds() // 3600)


def get_task_reminders(db: Session) -> Dict[str, List[Dict[str, Any]]]:
    """生成轻量级待办提醒，解决 HR 在企微/腾讯文档之间手工跟进易遗漏的问题。"""
    now = datetime.now()
    overdue_before = now - timedelta(hours=48)
    upcoming_before = now + timedelta(hours=24)
    feedback_before = now - timedelta(hours=24)
    offer_before = now - timedelta(days=3)

    overdue_candidates = []
    for candidate in (
        db.query(models.Candidate)
        .filter(models.Candidate.last_followup_at.isnot(None))
        .filter(models.Candidate.last_followup_at < overdue_before)
        .filter(~models.Candidate.stage.in_(TERMINAL_STAGES))
        .all()
    ):
        overdue_candidates.append(
            {
                "candidate_id": candidate.id,
                "candidate_name": candidate.name,
                "position_name": candidate.position_name,
                "stage": candidate.stage,
                "last_followup_at": candidate.last_followup_at,
                "interview_time": None,
                "interviewer": None,
                "overdue_hours": _hours_between(candidate.last_followup_at, now),
                "reminder_text": f"请及时跟进候选人{candidate.name}，当前阶段{candidate.stage}，已超过48小时未更新。",
            }
        )

    upcoming_interviews = []
    for interview in (
        db.query(models.Interview)
        .join(models.Candidate, models.Candidate.id == models.Interview.candidate_id)
        .filter(models.Interview.result == "PENDING")
        .filter(models.Interview.interview_time.isnot(None))
        .filter(models.Interview.interview_time >= now)
        .filter(models.Interview.interview_time <= upcoming_before)
        .all()
    ):
        candidate = interview.candidate
        upcoming_interviews.append(
            {
                "candidate_id": candidate.id,
                "candidate_name": candidate.name,
                "position_name": candidate.position_name,
                "stage": candidate.stage,
                "last_followup_at": candidate.last_followup_at,
                "interview_time": interview.interview_time,
                "interviewer": interview.interviewer,
                "overdue_hours": 0,
                "reminder_text": f"候选人{candidate.name}将在24小时内面试，请提醒面试官{interview.interviewer or '未填写'}。",
            }
        )

    interview_feedback_overdue = []
    for interview in (
        db.query(models.Interview)
        .join(models.Candidate, models.Candidate.id == models.Interview.candidate_id)
        .filter(models.Interview.result == "PENDING")
        .filter(models.Interview.interview_time.isnot(None))
        .filter(models.Interview.interview_time < feedback_before)
        .all()
    ):
        candidate = interview.candidate
        interview_feedback_overdue.append(
            {
                "candidate_id": candidate.id,
                "candidate_name": candidate.name,
                "position_name": candidate.position_name,
                "stage": candidate.stage,
                "last_followup_at": candidate.last_followup_at,
                "interview_time": interview.interview_time,
                "interviewer": interview.interviewer,
                "overdue_hours": _hours_between(interview.interview_time, now),
                "reminder_text": f"候选人{candidate.name}面试已超过24小时未反馈，请跟进面试官{interview.interviewer or '未填写'}。",
            }
        )

    offer_followup_overdue = []
    for candidate in (
        db.query(models.Candidate)
        .filter(models.Candidate.stage == "OFFER_SENT")
        .filter(models.Candidate.updated_at < offer_before)
        .all()
    ):
        offer_followup_overdue.append(
            {
                "candidate_id": candidate.id,
                "candidate_name": candidate.name,
                "position_name": candidate.position_name,
                "stage": candidate.stage,
                "last_followup_at": candidate.last_followup_at,
                "interview_time": None,
                "interviewer": None,
                "overdue_hours": _hours_between(candidate.updated_at, now),
                "reminder_text": f"候选人{candidate.name}Offer已发超过3天，请跟进入职意向。",
            }
        )

    return {
        "overdue_candidates": overdue_candidates,
        "upcoming_interviews": upcoming_interviews,
        "interview_feedback_overdue": interview_feedback_overdue,
        "offer_followup_overdue": offer_followup_overdue,
    }
