from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.constants import EventStatus
from app.schemas.confirmation import (
    ApproveActionRequest,
    ConfirmationActionResponse,
    PendingActionOut,
    RejectActionRequest,
)
from app.services import confirmation_service, event_service
from app.tools.recruitment_tools import RecruitmentToolExecutor

router = APIRouter(tags=["confirmations"])


@router.get("/pending", response_model=List[PendingActionOut])
def get_pending_actions(db: Session = Depends(get_db)):
    return confirmation_service.list_pending_actions(db)


@router.post("/{pending_action_id}/approve", response_model=ConfirmationActionResponse)
def approve_pending_action(
    pending_action_id: int,
    payload: ApproveActionRequest,
    db: Session = Depends(get_db),
):
    pending_action = confirmation_service.get_pending_action(db, pending_action_id)
    if not pending_action:
        raise HTTPException(status_code=404, detail="待确认动作不存在。")

    try:
        approved_action = confirmation_service.mark_action_approved(db, pending_action_id, payload.approved_by)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    result = RecruitmentToolExecutor().execute_confirmed_action(db, approved_action, payload.approved_by)
    db.refresh(approved_action)
    return ConfirmationActionResponse(
        success=result.success,
        message=result.message,
        pending_action=approved_action,
        executed_result=result.model_dump(mode="json"),
    )


@router.post("/{pending_action_id}/reject", response_model=ConfirmationActionResponse)
def reject_pending_action(
    pending_action_id: int,
    payload: RejectActionRequest,
    db: Session = Depends(get_db),
):
    pending_action = confirmation_service.get_pending_action(db, pending_action_id)
    if not pending_action:
        raise HTTPException(status_code=404, detail="待确认动作不存在。")

    try:
        rejected_action = confirmation_service.mark_action_rejected(
            db,
            pending_action_id,
            payload.approved_by,
            payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    event_service.create_event(
        db=db,
        raw_text=f"Reject pending action {pending_action_id}",
        intent=rejected_action.action_type,
        extracted_json=rejected_action.payload,
        confidence=1,
        status=EventStatus.FAILED,
        sender=payload.approved_by,
        source="CONFIRMATION",
        candidate_id=rejected_action.candidate_id,
        action_summary="HR 拒绝了待确认动作，主数据未变更。",
        error_message=payload.reason,
    )
    return ConfirmationActionResponse(
        success=True,
        message="已拒绝待确认动作，候选人状态不会变更。",
        pending_action=rejected_action,
        executed_result=None,
    )
