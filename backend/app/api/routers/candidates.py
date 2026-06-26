from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db import models
from app.schemas.candidate import CandidateOut
from app.schemas.resume import ResumeFileOut, ResumeScreeningReportOut
from app.services.candidate_service import list_candidates

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.get("", response_model=List[CandidateOut])
def get_candidates(db: Session = Depends(get_db)):
    return list_candidates(db)


@router.get("/{candidate_id}/resume")
def get_candidate_latest_resume(candidate_id: int, db: Session = Depends(get_db)):
    resume_file = (
        db.query(models.ResumeFile)
        .filter(models.ResumeFile.candidate_id == candidate_id)
        .order_by(models.ResumeFile.created_at.desc())
        .first()
    )
    if not resume_file:
        raise HTTPException(status_code=404, detail="Candidate resume not found")
    report = (
        db.query(models.ResumeScreeningReport)
        .filter(models.ResumeScreeningReport.resume_file_id == resume_file.id)
        .order_by(models.ResumeScreeningReport.created_at.desc())
        .first()
    )
    return {
        "resume_file": ResumeFileOut.model_validate(resume_file).model_dump(mode="json"),
        "screening_report": ResumeScreeningReportOut.model_validate(report).model_dump(mode="json") if report else None,
    }
