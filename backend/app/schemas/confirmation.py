from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class PendingActionOut(BaseModel):
    id: int
    candidate_id: Optional[int] = None
    action_type: str
    risk_level: str
    payload: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    status: str
    requested_by: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApproveActionRequest(BaseModel):
    approved_by: str = "HR负责人"


class RejectActionRequest(BaseModel):
    approved_by: str = "HR负责人"
    reason: Optional[str] = None


class ConfirmationActionResponse(BaseModel):
    success: bool
    message: str
    pending_action: Optional[PendingActionOut] = None
    executed_result: Optional[Dict[str, Any]] = None
