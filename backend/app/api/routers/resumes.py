from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.agents.agent_factory import get_recruitment_agent
from app.agents.resume_agent import ResumeAgent
from app.api.deps import get_db
from app.db import models
from app.schemas.resume import ResumeFileOut, ResumeScreenRequest, ResumeScreeningReportOut, ResumeUploadResponse
from app.services.candidate_merge_service import merge_resume_with_message
from app.services.event_service import create_event
from app.services.resume_file_service import (
    create_resume_file,
    find_resume_by_hash,
    get_resume_file,
    list_resume_files,
    remove_file_safely,
    save_upload_file,
    validate_pdf_upload,
)
from app.services.resume_parse_service import extract_text_from_pdf
from app.services.resume_screening_service import generate_screening_report

router = APIRouter()


@router.post("/upload", response_model=ResumeUploadResponse)
def upload_resume(
    file: UploadFile = File(...),
    message: Optional[str] = Form(None),
    sender: str = Form("HR小王"),
    source: str = Form("WEB_DEMO"),
    position_name: Optional[str] = Form(None),
    job_requirements: Optional[str] = Form(None),
    db: Session = Depends(get_db),
) -> ResumeUploadResponse:
    validate_pdf_upload(file)
    file_path, stored_filename, file_hash, file_size = save_upload_file(file)
    existing = find_resume_by_hash(db, file_hash)
    if existing:
        remove_file_safely(file_path)
        return ResumeUploadResponse(
            success=True,
            message="该简历文件已上传过，已返回已有解析记录。",
            candidate=_candidate_to_dict(existing.candidate) if existing.candidate else None,
            resume_file=ResumeFileOut.model_validate(existing).model_dump(mode="json"),
            resume_parse_result=existing.parsed_json,
            screening_report=_latest_report_dict(db, existing.id),
            warnings=["重复上传：file_hash 已存在"],
        )

    raw_text = ""
    parser_name = None
    try:
        raw_text, parser_name = extract_text_from_pdf(file_path)
    except Exception as exc:
        resume_file = create_resume_file(
            db=db,
            candidate_id=None,
            original_filename=file.filename or stored_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_hash=file_hash,
            mime_type=file.content_type,
            file_size=file_size,
            parse_status="FAILED",
            raw_text=None,
            parsed_json=None,
            resume_summary=None,
            skill_tags=None,
            confidence=0,
            error_message=str(exc),
            uploaded_by=sender,
            source=source,
        )
        create_event(
            db=db,
            raw_text=f"{message or ''} {file.filename or stored_filename}",
            intent="PARSE_RESUME",
            extracted_json={"error": str(exc)},
            confidence=0,
            status="FAILED",
            sender=sender,
            source=source,
            action_summary="简历 PDF 文本抽取失败",
            error_message=str(exc),
        )
        return ResumeUploadResponse(
            success=False,
            message="简历 PDF 文本抽取失败，已记录解析日志。",
            resume_file=ResumeFileOut.model_validate(resume_file).model_dump(mode="json"),
            warnings=[str(exc)],
        )

    if len(raw_text) < 100:
        resume_file = create_resume_file(
            db=db,
            candidate_id=None,
            original_filename=file.filename or stored_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_hash=file_hash,
            mime_type=file.content_type,
            file_size=file_size,
            parse_status="NEED_OCR",
            raw_text=raw_text,
            parsed_json=None,
            resume_summary=None,
            skill_tags=None,
            confidence=0,
            error_message="PDF 可抽取文本过少，可能是扫描件，当前低成本 Demo 不启用 OCR。",
            uploaded_by=sender,
            source=source,
        )
        create_event(
            db=db,
            raw_text=f"{message or ''} {file.filename or stored_filename}",
            intent="PARSE_RESUME",
            extracted_json={"parser": parser_name, "text_length": len(raw_text)},
            confidence=0,
            status="NEED_OCR",
            sender=sender,
            source=source,
            action_summary="PDF 文本过少，需要 OCR 后再解析",
            error_message="NEED_OCR",
        )
        return ResumeUploadResponse(
            success=True,
            message="PDF 文本过少，疑似扫描件，已标记 NEED_OCR。",
            resume_file=ResumeFileOut.model_validate(resume_file).model_dump(mode="json"),
            warnings=["PDF 可抽取文本过少，企业版可接 OCR 或对象存储解析服务"],
        )

    message_agent_result = get_recruitment_agent().parse_message(message) if message else None
    resume_parse_result = ResumeAgent().parse_resume(raw_text)
    final_position_name = position_name or (message_agent_result.candidate.position_name if message_agent_result else None)
    candidate, warnings, need_review = merge_resume_with_message(
        db=db,
        message_agent_result=message_agent_result,
        resume_parse_result=resume_parse_result,
        position_name=final_position_name,
        sender=sender,
        source=source,
    )
    warnings.extend(resume_parse_result.warnings)
    parse_status = "NEED_REVIEW" if need_review or resume_parse_result.need_manual_review else "SUCCESS"

    resume_file = create_resume_file(
        db=db,
        candidate_id=candidate.id,
        original_filename=file.filename or stored_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_hash=file_hash,
        mime_type=file.content_type,
        file_size=file_size,
        parse_status=parse_status,
        raw_text=raw_text,
        parsed_json=resume_parse_result.model_dump(mode="json"),
        resume_summary=resume_parse_result.resume_summary,
        skill_tags=resume_parse_result.skills,
        confidence=resume_parse_result.confidence,
        error_message="; ".join(warnings) if warnings else None,
        uploaded_by=sender,
        source=source,
    )
    candidate.latest_resume_id = resume_file.id
    candidate.resume_parse_status = parse_status
    db.commit()
    db.refresh(candidate)

    screening_report = generate_screening_report(
        db=db,
        candidate=candidate,
        resume_file=resume_file,
        resume_parse_result=resume_parse_result,
        position_name=final_position_name,
        job_requirements=job_requirements,
    )

    event_status = "NEED_REVIEW" if parse_status == "NEED_REVIEW" else "SUCCESS"
    create_event(
        db=db,
        candidate_id=candidate.id,
        raw_text=f"{message or ''} {file.filename or stored_filename}",
        intent="CREATE_CANDIDATE_WITH_RESUME" if message else "PARSE_RESUME",
        extracted_json={
            "message_agent_result": message_agent_result.model_dump(mode="json") if message_agent_result else None,
            "resume_parse_result": resume_parse_result.model_dump(mode="json"),
            "parser": parser_name,
            "warnings": warnings,
        },
        confidence=resume_parse_result.confidence,
        status=event_status,
        sender=sender,
        source=source,
        action_summary="简历 PDF 已解析并合并候选人档案",
        error_message="; ".join(warnings) if warnings else None,
    )
    _create_sync_log(
        db,
        target="TENCENT_DOC",
        operation="UPSERT_CANDIDATE_WITH_RESUME",
        payload={
            "candidate_id": candidate.id,
            "resume_file_id": resume_file.id,
            "position_name": final_position_name,
            "match_score": screening_report.match_score,
            "skill_tags": resume_parse_result.skills,
        },
        status="SUCCESS",
    )

    return ResumeUploadResponse(
        success=True,
        message="简历已解析，并与候选人招聘台账合并。" if not warnings else "简历已解析，但存在需要复核的信息。",
        candidate=_candidate_to_dict(candidate),
        resume_file=ResumeFileOut.model_validate(resume_file).model_dump(mode="json"),
        resume_parse_result=resume_parse_result.model_dump(mode="json"),
        screening_report=ResumeScreeningReportOut.model_validate(screening_report).model_dump(mode="json"),
        warnings=warnings,
    )


@router.get("", response_model=List[ResumeFileOut])
def get_resumes(db: Session = Depends(get_db)):
    return list_resume_files(db)


@router.get("/{resume_id}", response_model=ResumeFileOut)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    resume_file = get_resume_file(db, resume_id)
    if not resume_file:
        raise HTTPException(status_code=404, detail="Resume file not found")
    return resume_file


@router.post("/{resume_id}/reparse", response_model=ResumeUploadResponse)
def reparse_resume(resume_id: int, db: Session = Depends(get_db)) -> ResumeUploadResponse:
    resume_file = get_resume_file(db, resume_id)
    if not resume_file:
        raise HTTPException(status_code=404, detail="Resume file not found")
    raw_text = resume_file.raw_text
    if not raw_text:
        raw_text, _ = extract_text_from_pdf(resume_file.file_path)
    if len(raw_text or "") < 100:
        resume_file.parse_status = "NEED_OCR"
        resume_file.error_message = "PDF 可抽取文本过少，需要 OCR"
        db.commit()
        db.refresh(resume_file)
        return ResumeUploadResponse(
            success=True,
            message="PDF 文本过少，已标记 NEED_OCR。",
            resume_file=ResumeFileOut.model_validate(resume_file).model_dump(mode="json"),
            warnings=["需要 OCR 后再解析"],
        )

    result = ResumeAgent().parse_resume(raw_text)
    resume_file.raw_text = raw_text
    resume_file.parsed_json = result.model_dump(mode="json")
    resume_file.resume_summary = result.resume_summary
    resume_file.skill_tags = result.skills
    resume_file.confidence = result.confidence
    resume_file.parse_status = "NEED_REVIEW" if result.need_manual_review else "SUCCESS"
    resume_file.error_message = "; ".join(result.warnings) if result.warnings else None
    if resume_file.candidate:
        candidate = resume_file.candidate
        candidate.skills = result.skills
        candidate.resume_summary = result.resume_summary
        candidate.resume_parse_status = resume_file.parse_status
        candidate.latest_resume_id = resume_file.id
    db.commit()
    db.refresh(resume_file)
    return ResumeUploadResponse(
        success=True,
        message="简历已重新解析。",
        candidate=_candidate_to_dict(resume_file.candidate) if resume_file.candidate else None,
        resume_file=ResumeFileOut.model_validate(resume_file).model_dump(mode="json"),
        resume_parse_result=result.model_dump(mode="json"),
        warnings=result.warnings,
    )


@router.post("/{resume_id}/screen", response_model=ResumeScreeningReportOut)
def screen_resume(resume_id: int, payload: ResumeScreenRequest, db: Session = Depends(get_db)):
    resume_file = get_resume_file(db, resume_id)
    if not resume_file or not resume_file.candidate:
        raise HTTPException(status_code=404, detail="Resume file or candidate not found")
    if not resume_file.parsed_json:
        raise HTTPException(status_code=400, detail="Resume has no parsed_json; please reparse first")
    from app.schemas.resume import ResumeParseResult

    parse_result = ResumeParseResult.model_validate(resume_file.parsed_json)
    report = generate_screening_report(
        db=db,
        candidate=resume_file.candidate,
        resume_file=resume_file,
        resume_parse_result=parse_result,
        position_name=payload.position_name,
        job_requirements=payload.job_requirements,
    )
    return report


def _latest_report_dict(db: Session, resume_file_id: int) -> Optional[Dict[str, Any]]:
    report = (
        db.query(models.ResumeScreeningReport)
        .filter(models.ResumeScreeningReport.resume_file_id == resume_file_id)
        .order_by(models.ResumeScreeningReport.created_at.desc())
        .first()
    )
    if not report:
        return None
    return ResumeScreeningReportOut.model_validate(report).model_dump(mode="json")


def _candidate_to_dict(candidate: Optional[models.Candidate]) -> Optional[Dict[str, Any]]:
    if not candidate:
        return None
    return {
        "id": candidate.id,
        "name": candidate.name,
        "phone": candidate.phone,
        "email": candidate.email,
        "position_name": candidate.position_name,
        "education": candidate.education,
        "school": candidate.school,
        "major": candidate.major,
        "graduation_year": candidate.graduation_year,
        "work_years": candidate.work_years,
        "skills": candidate.skills,
        "resume_summary": candidate.resume_summary,
        "resume_parse_status": candidate.resume_parse_status,
        "latest_resume_id": candidate.latest_resume_id,
        "match_score": candidate.match_score,
        "match_level": candidate.match_level,
        "stage": candidate.stage,
        "source": candidate.source,
    }


def _create_sync_log(db: Session, target: str, operation: str, payload: Dict[str, Any], status: str) -> None:
    sync_log = models.SyncLog(target=target, operation=operation, payload=payload, status=status)
    db.add(sync_log)
    db.commit()

