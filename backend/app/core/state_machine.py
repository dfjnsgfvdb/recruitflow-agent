from dataclasses import dataclass
from typing import Dict, Optional, Set

from app.core.constants import RecruitmentStage


ALLOWED_STAGE_TRANSITIONS: Dict[str, Set[str]] = {
    RecruitmentStage.NEW: {
        RecruitmentStage.SCREENING,
        RecruitmentStage.RESUME_PASSED,
        RecruitmentStage.RESUME_REJECTED,
    },
    RecruitmentStage.SCREENING: {
        RecruitmentStage.RESUME_PASSED,
        RecruitmentStage.RESUME_REJECTED,
    },
    RecruitmentStage.RESUME_PASSED: {RecruitmentStage.FIRST_INTERVIEW_PENDING},
    RecruitmentStage.FIRST_INTERVIEW_PENDING: {
        RecruitmentStage.FIRST_INTERVIEW_PASSED,
        RecruitmentStage.FIRST_INTERVIEW_REJECTED,
        RecruitmentStage.REJECTED,
    },
    RecruitmentStage.FIRST_INTERVIEW_PASSED: {RecruitmentStage.SECOND_INTERVIEW_PENDING},
    RecruitmentStage.SECOND_INTERVIEW_PENDING: {
        RecruitmentStage.SECOND_INTERVIEW_PASSED,
        RecruitmentStage.REJECTED,
    },
    RecruitmentStage.SECOND_INTERVIEW_PASSED: {RecruitmentStage.OFFER_PENDING},
    RecruitmentStage.OFFER_PENDING: {RecruitmentStage.OFFER_SENT},
    RecruitmentStage.OFFER_SENT: {RecruitmentStage.HIRED, RecruitmentStage.REJECTED},
    RecruitmentStage.RESUME_REJECTED: set(),
    RecruitmentStage.FIRST_INTERVIEW_REJECTED: set(),
    RecruitmentStage.REJECTED: set(),
    RecruitmentStage.HIRED: set(),
}


@dataclass
class StageTransitionCheckResult:
    allowed: bool
    need_confirmation: bool
    reason: str
    current_stage: Optional[str]
    target_stage: Optional[str]


def check_stage_transition(current_stage: Optional[str], target_stage: Optional[str]) -> StageTransitionCheckResult:
    if not target_stage:
        return StageTransitionCheckResult(
            allowed=False,
            need_confirmation=False,
            reason="目标招聘阶段为空，无法更新状态。",
            current_stage=current_stage,
            target_stage=target_stage,
        )

    normalized_current = current_stage or RecruitmentStage.NEW
    if normalized_current == target_stage:
        return StageTransitionCheckResult(
            allowed=True,
            need_confirmation=False,
            reason="目标阶段与当前阶段一致，无需额外确认。",
            current_stage=normalized_current,
            target_stage=target_stage,
        )

    allowed_targets = ALLOWED_STAGE_TRANSITIONS.get(normalized_current, set())
    if target_stage in allowed_targets:
        return StageTransitionCheckResult(
            allowed=True,
            need_confirmation=False,
            reason="状态流转符合招聘状态机。",
            current_stage=normalized_current,
            target_stage=target_stage,
        )

    if target_stage in {RecruitmentStage.REJECTED, RecruitmentStage.OFFER_SENT, RecruitmentStage.HIRED}:
        return StageTransitionCheckResult(
            allowed=False,
            need_confirmation=True,
            reason="目标阶段属于高风险阶段，需要 HR 确认后执行。",
            current_stage=normalized_current,
            target_stage=target_stage,
        )

    return StageTransitionCheckResult(
        allowed=False,
        need_confirmation=True,
        reason="检测到不符合状态机的阶段跳跃或回退，需要 HR 确认。",
        current_stage=normalized_current,
        target_stage=target_stage,
    )


def infer_stage_from_interview_round(round_value: Optional[str]) -> Optional[str]:
    if round_value == "FIRST":
        return RecruitmentStage.FIRST_INTERVIEW_PENDING
    if round_value == "SECOND":
        return RecruitmentStage.SECOND_INTERVIEW_PENDING
    # HR / FINAL 的业务含义更接近 Offer 决策，但 Demo 阶段不自动推断，避免模型误判导致状态跳跃。
    return None
