from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class RecruitmentEventOut(BaseModel):
    id: int
    candidate_id: Optional[int] = None
    intent: str
    raw_text: str
    extracted_json: Optional[Dict[str, Any]] = None
    confidence: float
    action_summary: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    sender: Optional[str] = None
    source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
