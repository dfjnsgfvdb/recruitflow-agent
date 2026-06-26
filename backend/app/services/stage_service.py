from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import EventStatus, RiskLevel, ToolName
from app.core.state_machine import check_stage_transition
from app.db import models
from app.tools.tool_result import ToolExecutionResult


def update_candidate_stage_with_check(
    db: Session,
    candidate: models.Candidate,
    target_stage: Optional[str],
    reason: Optional[str] = None,
) -> ToolExecutionResult:
    # 状态机是主数据安全边界：模型抽取出的 new_stage 必须先校验，不能直接写库。
    check_result = check_stage_transition(candidate.stage, target_stage)
    if check_result.allowed:
        candidate.stage = target_stage
        candidate.last_followup_at = datetime.now()
        db.commit()
        db.refresh(candidate)
        return ToolExecutionResult(
            tool=ToolName.UPDATE_CANDIDATE_STAGE,
            success=True,
            status=EventStatus.SUCCESS,
            message=reason or check_result.reason,
            data={"candidate_id": candidate.id, "stage": candidate.stage},
            risk_level=RiskLevel.MEDIUM,
        )

    if check_result.need_confirmation:
        return ToolExecutionResult(
            tool=ToolName.UPDATE_CANDIDATE_STAGE,
            success=False,
            status=EventStatus.NEED_CONFIRMATION,
            message=check_result.reason,
            data={
                "candidate_id": candidate.id,
                "current_stage": check_result.current_stage,
                "target_stage": check_result.target_stage,
            },
            risk_level=RiskLevel.MEDIUM,
            need_confirmation=True,
        )

    return ToolExecutionResult(
        tool=ToolName.UPDATE_CANDIDATE_STAGE,
        success=False,
        status=EventStatus.FAILED,
        message=check_result.reason,
        data={"candidate_id": candidate.id, "target_stage": target_stage},
        risk_level=RiskLevel.MEDIUM,
        error_message=check_result.reason,
    )
