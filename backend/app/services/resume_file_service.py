import hashlib
import os
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import models

UPLOAD_DIR = Path("uploads/resumes")
MAX_RESUME_SIZE = 10 * 1024 * 1024


def ensure_resume_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def validate_pdf_upload(file: UploadFile) -> None:
    filename = file.filename or ""
    content_type = (file.content_type or "").lower()
    if not filename.lower().endswith(".pdf") and content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=400, detail="只允许上传 PDF 简历文件")


def save_upload_file(file: UploadFile) -> Tuple[str, str, str, int]:
    """保存上传文件并计算 hash。文件名重生成，避免使用用户原始文件名带来的安全风险。"""
    ensure_resume_upload_dir()
    suffix = ".pdf"
    stored_filename = f"{uuid4().hex}{suffix}"
    file_path = UPLOAD_DIR / stored_filename
    digest = hashlib.sha256()
    total_size = 0

    with file_path.open("wb") as target:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_RESUME_SIZE:
                target.close()
                try:
                    file_path.unlink(missing_ok=True)
                except TypeError:
                    if file_path.exists():
                        file_path.unlink()
                raise HTTPException(status_code=400, detail="简历文件不能超过 10MB")
            digest.update(chunk)
            target.write(chunk)

    return str(file_path), stored_filename, digest.hexdigest(), total_size


def remove_file_safely(file_path: str) -> None:
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
    except Exception:
        pass


def find_resume_by_hash(db: Session, file_hash: str) -> Optional[models.ResumeFile]:
    return db.query(models.ResumeFile).filter(models.ResumeFile.file_hash == file_hash).first()


def create_resume_file(
    db: Session,
    candidate_id: Optional[int],
    original_filename: str,
    stored_filename: str,
    file_path: str,
    file_hash: str,
    mime_type: Optional[str],
    file_size: Optional[int],
    parse_status: str,
    raw_text: Optional[str],
    parsed_json: Optional[dict],
    resume_summary: Optional[str],
    skill_tags: Optional[list],
    confidence: float,
    error_message: Optional[str],
    uploaded_by: Optional[str],
    source: str,
) -> models.ResumeFile:
    resume_file = models.ResumeFile(
        candidate_id=candidate_id,
        original_filename=os.path.basename(original_filename),
        stored_filename=stored_filename,
        file_path=file_path,
        file_hash=file_hash,
        mime_type=mime_type,
        file_size=file_size,
        parse_status=parse_status,
        raw_text=raw_text,
        parsed_json=parsed_json,
        resume_summary=resume_summary,
        skill_tags=skill_tags,
        confidence=confidence,
        error_message=error_message,
        uploaded_by=uploaded_by,
        source=source,
    )
    db.add(resume_file)
    db.commit()
    db.refresh(resume_file)
    return resume_file


def list_resume_files(db: Session, limit: int = 100):
    return db.query(models.ResumeFile).order_by(models.ResumeFile.created_at.desc()).limit(limit).all()


def get_resume_file(db: Session, resume_id: int) -> Optional[models.ResumeFile]:
    return db.query(models.ResumeFile).filter(models.ResumeFile.id == resume_id).first()
