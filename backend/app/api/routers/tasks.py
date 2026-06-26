from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.task_service import get_task_reminders

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/reminders")
def reminders(db: Session = Depends(get_db)):
    return get_task_reminders(db)
