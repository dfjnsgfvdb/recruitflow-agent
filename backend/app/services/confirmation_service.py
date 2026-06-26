from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.constants import PendingActionStatus
from app.db import models


def create_pending_action(
    db: Session,
    candidate_id: Optional[int],
    action_type: str,
    risk_level: str,
    payload: Optional[Dict[str, Any]],
    reason: Optional[str],
    requested_by: Optional[str],
) -> models.PendingAction:
    pending_action = models.PendingAction(
        candidate_id=candidate_id,
        action_type=action_type,
        risk_level=risk_level,
        payload=payload,
        reason=reason,
        requested_by=requested_by,
        status=PendingActionStatus.PENDING,
    )
    db.add(pending_action)
    db.commit()
    db.refresh(pending_action)
    return pending_action


def list_pending_actions(db: Session):
    return (
        db.query(models.PendingAction)
        .filter(models.PendingAction.status == PendingActionStatus.PENDING)
        .order_by(models.PendingAction.created_at.desc())
        .all()
    )


def get_pending_action(db: Session, pending_action_id: int):
    return db.query(models.PendingAction).filter(models.PendingAction.id == pending_action_id).first()


def _ensure_pending(pending_action: models.PendingAction) -> None:
    if pending_action.status != PendingActionStatus.PENDING:
        raise ValueError("该待确认动作已处理，不能重复确认或拒绝。")


def mark_action_rejected(
    db: Session,
    pending_action_id: int,
    approved_by: str,
    reason: Optional[str] = None,
):
    pending_action = get_pending_action(db, pending_action_id)
    if not pending_action:
        return None
    _ensure_pending(pending_action)
    pending_action.status = PendingActionStatus.REJECTED
    pending_action.approved_by = approved_by
    if reason:
        pending_action.reason = f"{pending_action.reason or ''}\n拒绝原因：{reason}".strip()
    db.commit()
    db.refresh(pending_action)
    return pending_action


def mark_action_approved(db: Session, pending_action_id: int, approved_by: str):
    pending_action = get_pending_action(db, pending_action_id)
    if not pending_action:
        return None
    _ensure_pending(pending_action)
    pending_action.status = PendingActionStatus.APPROVED
    pending_action.approved_by = approved_by
    db.commit()
    db.refresh(pending_action)
    return pending_action


def mark_action_executed(db: Session, pending_action_id: int):
    pending_action = get_pending_action(db, pending_action_id)
    if not pending_action:
        return None
    pending_action.status = PendingActionStatus.EXECUTED
    db.commit()
    db.refresh(pending_action)
    return pending_action


def mark_action_failed(db: Session, pending_action_id: int, error_message: str):
    pending_action = get_pending_action(db, pending_action_id)
    if not pending_action:
        return None
    pending_action.status = PendingActionStatus.FAILED
    pending_action.reason = f"{pending_action.reason or ''}\n执行失败：{error_message}".strip()
    db.commit()
    db.refresh(pending_action)
    return pending_action
