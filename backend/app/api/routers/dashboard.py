from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import get_dashboard_summary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    return get_dashboard_summary(db)
