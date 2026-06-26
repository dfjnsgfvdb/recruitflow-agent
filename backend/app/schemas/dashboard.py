from pydantic import BaseModel
from typing import List

from app.schemas.event import RecruitmentEventOut


class StageDistributionItem(BaseModel):
    stage: str
    count: int


class PositionDistributionItem(BaseModel):
    position_name: str
    count: int


class DashboardSummary(BaseModel):
    total_candidates: int
    today_new_candidates: int
    pending_interviews: int
    offer_count: int
    timeout_followup_count: int
    pending_confirmation_count: int = 0
    overdue_candidate_count: int = 0
    upcoming_interview_count: int = 0
    sync_success_count: int = 0
    sync_failed_count: int = 0
    low_confidence_event_count: int = 0
    stage_distribution: List[StageDistributionItem]
    position_distribution: List[PositionDistributionItem]
    recent_events: List[RecruitmentEventOut]
