from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class SyncLogOut(BaseModel):
    id: int
    target: str
    operation: str
    payload: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
