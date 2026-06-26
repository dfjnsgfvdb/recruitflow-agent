from sqlalchemy.orm import Session

from app.db import models


def list_sync_logs(db: Session, limit: int = 100):
    return db.query(models.SyncLog).order_by(models.SyncLog.created_at.desc()).limit(limit).all()
