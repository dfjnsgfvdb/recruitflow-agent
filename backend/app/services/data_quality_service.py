from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import models


def get_data_quality_summary(db: Session) -> Dict[str, List[Dict[str, Any]]]:
    """输出数据质量问题，帮助 HR 发现企微消息自动抽取后的缺失字段和疑似重复数据。"""
    missing_phone_candidates = [
        _candidate_item(candidate)
        for candidate in db.query(models.Candidate).filter((models.Candidate.phone.is_(None)) | (models.Candidate.phone == "")).all()
    ]
    missing_position_candidates = [
        _candidate_item(candidate)
        for candidate in db.query(models.Candidate)
        .filter((models.Candidate.position_name.is_(None)) | (models.Candidate.position_name == ""))
        .all()
    ]
    missing_interviewer_interviews = [
        {
            "interview_id": interview.id,
            "candidate_id": interview.candidate_id,
            "candidate_name": interview.candidate.name if interview.candidate else None,
            "round": interview.round,
            "interview_time": interview.interview_time,
            "result": interview.result,
        }
        for interview in db.query(models.Interview)
        .filter(models.Interview.result == "PENDING")
        .filter((models.Interview.interviewer.is_(None)) | (models.Interview.interviewer == ""))
        .all()
    ]
    low_confidence_events = [
        {
            "id": event.id,
            "intent": event.intent,
            "confidence": event.confidence,
            "status": event.status,
            "raw_text": event.raw_text,
            "created_at": event.created_at,
        }
        for event in db.query(models.RecruitmentEvent).filter(models.RecruitmentEvent.confidence < 0.7).order_by(models.RecruitmentEvent.created_at.desc()).all()
    ]

    duplicate_candidate_groups = []
    phone_rows = (
        db.query(models.Candidate.phone, func.count(models.Candidate.id))
        .filter(models.Candidate.phone.isnot(None), models.Candidate.phone != "")
        .group_by(models.Candidate.phone)
        .having(func.count(models.Candidate.id) > 1)
        .all()
    )
    for phone, count in phone_rows:
        candidates = db.query(models.Candidate).filter(models.Candidate.phone == phone).all()
        duplicate_candidate_groups.append(
            {"group_key": f"phone:{phone}", "count": count, "candidates": [_candidate_item(candidate) for candidate in candidates]}
        )

    name_position_rows = (
        db.query(models.Candidate.name, models.Candidate.position_name, func.count(models.Candidate.id))
        .filter((models.Candidate.phone.is_(None)) | (models.Candidate.phone == ""))
        .filter(models.Candidate.position_name.isnot(None), models.Candidate.position_name != "")
        .group_by(models.Candidate.name, models.Candidate.position_name)
        .having(func.count(models.Candidate.id) > 1)
        .all()
    )
    for name, position_name, count in name_position_rows:
        candidates = (
            db.query(models.Candidate)
            .filter(models.Candidate.name == name, models.Candidate.position_name == position_name)
            .filter((models.Candidate.phone.is_(None)) | (models.Candidate.phone == ""))
            .all()
        )
        duplicate_candidate_groups.append(
            {
                "group_key": f"name_position:{name}:{position_name}",
                "count": count,
                "candidates": [_candidate_item(candidate) for candidate in candidates],
            }
        )

    candidates_without_resume = [
        _candidate_item(candidate)
        for candidate in db.query(models.Candidate).filter(~models.Candidate.resume_files.any()).all()
    ]
    resume_parse_failed = [_resume_item(resume) for resume in db.query(models.ResumeFile).filter(models.ResumeFile.parse_status == "FAILED").all()]
    resume_need_ocr = [_resume_item(resume) for resume in db.query(models.ResumeFile).filter(models.ResumeFile.parse_status == "NEED_OCR").all()]
    resume_need_review = [
        _resume_item(resume) for resume in db.query(models.ResumeFile).filter(models.ResumeFile.parse_status == "NEED_REVIEW").all()
    ]
    contact_conflicts = [
        _resume_item(resume)
        for resume in db.query(models.ResumeFile)
        .filter(models.ResumeFile.parse_status == "NEED_REVIEW")
        .filter(models.ResumeFile.error_message.isnot(None))
        .filter(
            (models.ResumeFile.error_message.like("%手机号%"))
            | (models.ResumeFile.error_message.like("%邮箱%"))
            | (models.ResumeFile.error_message.like("%contact%"))
        )
        .all()
    ]
    low_match_score_but_resume_passed = [
        _candidate_item(candidate)
        for candidate in db.query(models.Candidate)
        .filter(models.Candidate.stage == "RESUME_PASSED")
        .filter(models.Candidate.match_score.isnot(None))
        .filter(models.Candidate.match_score < 60)
        .all()
    ]

    return {
        "missing_phone_candidates": missing_phone_candidates,
        "missing_position_candidates": missing_position_candidates,
        "missing_interviewer_interviews": missing_interviewer_interviews,
        "low_confidence_events": low_confidence_events,
        "duplicate_candidate_groups": duplicate_candidate_groups,
        "candidates_without_resume": candidates_without_resume,
        "resume_parse_failed": resume_parse_failed,
        "resume_need_ocr": resume_need_ocr,
        "resume_need_review": resume_need_review,
        "contact_conflicts": contact_conflicts,
        "low_match_score_but_resume_passed": low_match_score_but_resume_passed,
    }


def _candidate_item(candidate: models.Candidate) -> Dict[str, Any]:
    return {
        "id": candidate.id,
        "name": candidate.name,
        "phone": candidate.phone,
        "position_name": candidate.position_name,
        "stage": candidate.stage,
        "source": candidate.source,
        "created_at": candidate.created_at,
        "updated_at": candidate.updated_at,
        "resume_parse_status": candidate.resume_parse_status,
        "latest_resume_id": candidate.latest_resume_id,
        "match_score": candidate.match_score,
        "match_level": candidate.match_level,
    }


def _resume_item(resume: models.ResumeFile) -> Dict[str, Any]:
    return {
        "id": resume.id,
        "candidate_id": resume.candidate_id,
        "candidate_name": resume.candidate.name if resume.candidate else None,
        "original_filename": resume.original_filename,
        "parse_status": resume.parse_status,
        "confidence": resume.confidence,
        "error_message": resume.error_message,
        "created_at": resume.created_at,
    }
