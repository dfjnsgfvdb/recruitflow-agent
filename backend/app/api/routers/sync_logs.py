from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.sync_log import SyncLogOut
from app.services.sync_log_service import list_sync_logs

router = APIRouter(prefix="/api/sync-logs", tags=["sync-logs"])


@router.get("", response_model=List[SyncLogOut])
def get_sync_logs(db: Session = Depends(get_db)):
    return list_sync_logs(db, limit=100)
