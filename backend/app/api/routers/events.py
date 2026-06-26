from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.event import RecruitmentEventOut
from app.services.event_service import list_events

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=List[RecruitmentEventOut])
def get_events(db: Session = Depends(get_db)):
    return list_events(db)
