from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.interview import InterviewOut
from app.services.interview_service import list_interviews

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


@router.get("", response_model=List[InterviewOut])
def get_interviews(db: Session = Depends(get_db)):
    return list_interviews(db)
