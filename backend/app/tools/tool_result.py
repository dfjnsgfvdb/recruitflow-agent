from typing import Any, Optional

from pydantic import BaseModel

from app.core.constants import EventStatus, RiskLevel


class ToolExecutionResult(BaseModel):
    tool: str
    success: bool
    status: str = EventStatus.SUCCESS
    message: str
    data: Optional[Any] = None
    risk_level: str = RiskLevel.LOW
    need_confirmation: bool = False
    pending_action_id: Optional[int] = None
    error_message: Optional[str] = None
