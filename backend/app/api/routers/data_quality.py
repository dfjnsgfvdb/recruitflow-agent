from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.data_quality_service import get_data_quality_summary

router = APIRouter(prefix="/api/data-quality", tags=["data-quality"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return get_data_quality_summary(db)
