from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.constants import PendingActionStatus
from app.db import models
from app.schemas.dashboard import DashboardSummary, PositionDistributionItem, StageDistributionItem


def get_dashboard_summary(db: Session) -> DashboardSummary:
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    now = datetime.now()
    timeout_before = now - timedelta(hours=48)

    total_candidates = db.query(models.Candidate).count()
    today_new_candidates = db.query(models.Candidate).filter(models.Candidate.created_at >= today_start).count()
    pending_interviews = db.query(models.Interview).filter(models.Interview.result == "PENDING").count()
    offer_count = db.query(models.Candidate).filter(models.Candidate.stage.in_(["OFFER_PENDING", "OFFER_SENT"])).count()
    timeout_followup_count = (
        db.query(models.Candidate)
        .filter(models.Candidate.last_followup_at.isnot(None), models.Candidate.last_followup_at < timeout_before)
        .count()
    )
    pending_confirmation_count = (
        db.query(models.PendingAction).filter(models.PendingAction.status == PendingActionStatus.PENDING).count()
    )
    upcoming_interview_count = (
        db.query(models.Interview)
        .filter(models.Interview.result == "PENDING")
        .filter(models.Interview.interview_time.isnot(None))
        .filter(models.Interview.interview_time >= now)
        .filter(models.Interview.interview_time <= now + timedelta(hours=24))
        .count()
    )
    sync_success_count = db.query(models.SyncLog).filter(models.SyncLog.status == "SUCCESS").count()
    sync_failed_count = db.query(models.SyncLog).filter(models.SyncLog.status == "FAILED").count()
    low_confidence_event_count = db.query(models.RecruitmentEvent).filter(models.RecruitmentEvent.confidence < 0.7).count()

    stage_rows = (
        db.query(models.Candidate.stage, func.count(models.Candidate.id))
        .group_by(models.Candidate.stage)
        .order_by(func.count(models.Candidate.id).desc())
        .all()
    )
    position_rows = (
        db.query(models.Candidate.position_name, func.count(models.Candidate.id))
        .filter(models.Candidate.position_name.isnot(None))
        .group_by(models.Candidate.position_name)
        .order_by(func.count(models.Candidate.id).desc())
        .all()
    )
    recent_events = db.query(models.RecruitmentEvent).order_by(models.RecruitmentEvent.created_at.desc()).limit(10).all()

    return DashboardSummary(
        total_candidates=total_candidates,
        today_new_candidates=today_new_candidates,
        pending_interviews=pending_interviews,
        offer_count=offer_count,
        timeout_followup_count=timeout_followup_count,
        pending_confirmation_count=pending_confirmation_count,
        overdue_candidate_count=timeout_followup_count,
        upcoming_interview_count=upcoming_interview_count,
        sync_success_count=sync_success_count,
        sync_failed_count=sync_failed_count,
        low_confidence_event_count=low_confidence_event_count,
        stage_distribution=[StageDistributionItem(stage=stage or "UNKNOWN", count=count) for stage, count in stage_rows],
        position_distribution=[
            PositionDistributionItem(position_name=position_name or "未填写", count=count)
            for position_name, count in position_rows
        ],
        recent_events=recent_events,
    )
