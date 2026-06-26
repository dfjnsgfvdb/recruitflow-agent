from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.mysql import JSON, LONGTEXT
from sqlalchemy.orm import relationship

from app.db.database import Base


class Position(Base):
    __tablename__ = "positions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, index=True)
    department = Column(String(128), nullable=True)
    owner = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default="OPEN")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    candidates = relationship("Candidate", back_populates="position")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, index=True)
    phone = Column(String(32), nullable=True, index=True)
    email = Column(String(128), nullable=True, index=True)
    position_id = Column(BigInteger, ForeignKey("positions.id"), nullable=True)
    position_name = Column(String(128), nullable=True, index=True)
    source = Column(String(64), nullable=True)
    education = Column(String(64), nullable=True)
    school = Column(String(128), nullable=True)
    major = Column(String(128), nullable=True)
    graduation_year = Column(String(32), nullable=True)
    work_years = Column(String(64), nullable=True)
    skills = Column(JSON, nullable=True)
    experience_summary = Column(Text, nullable=True)
    resume_summary = Column(Text, nullable=True)
    resume_parse_status = Column(String(32), nullable=True)
    latest_resume_id = Column(BigInteger, nullable=True)
    match_score = Column(Float, nullable=True)
    match_level = Column(String(32), nullable=True)
    stage = Column(String(64), nullable=False, default="NEW", index=True)
    owner = Column(String(64), nullable=True)
    last_followup_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    position = relationship("Position", back_populates="candidates")
    interviews = relationship("Interview", back_populates="candidate", cascade="all, delete-orphan")
    events = relationship("RecruitmentEvent", back_populates="candidate")
    pending_actions = relationship("PendingAction", back_populates="candidate")
    resume_files = relationship("ResumeFile", back_populates="candidate")
    screening_reports = relationship("ResumeScreeningReport", back_populates="candidate")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    candidate_id = Column(BigInteger, ForeignKey("candidates.id"), nullable=False, index=True)
    round = Column(String(32), nullable=True)
    interview_time = Column(DateTime, nullable=True, index=True)
    interviewer = Column(String(64), nullable=True)
    location = Column(String(128), nullable=True)
    result = Column(String(32), nullable=False, default="PENDING")
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    candidate = relationship("Candidate", back_populates="interviews")


class RecruitmentEvent(Base):
    __tablename__ = "recruitment_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    candidate_id = Column(BigInteger, ForeignKey("candidates.id"), nullable=True, index=True)
    intent = Column(String(64), nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    extracted_json = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=False, default=0)
    action_summary = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="SUCCESS", index=True)
    error_message = Column(Text, nullable=True)
    sender = Column(String(64), nullable=True)
    source = Column(String(64), nullable=False, default="WEB_DEMO")
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    candidate = relationship("Candidate", back_populates="events")


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    target = Column(String(64), nullable=False)
    operation = Column(String(64), nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False, default="SUCCESS")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class PendingAction(Base):
    __tablename__ = "pending_actions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    candidate_id = Column(BigInteger, ForeignKey("candidates.id"), nullable=True, index=True)
    action_type = Column(String(64), nullable=False, index=True)
    risk_level = Column(String(32), nullable=False, default="HIGH")
    payload = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="PENDING", index=True)
    requested_by = Column(String(64), nullable=True)
    approved_by = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    candidate = relationship("Candidate", back_populates="pending_actions")


class ResumeFile(Base):
    __tablename__ = "resume_files"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    candidate_id = Column(BigInteger, ForeignKey("candidates.id"), nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_hash = Column(String(128), nullable=False, index=True)
    mime_type = Column(String(128), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    parse_status = Column(String(32), nullable=False, default="PENDING", index=True)
    raw_text = Column(LONGTEXT, nullable=True)
    parsed_json = Column(JSON, nullable=True)
    resume_summary = Column(Text, nullable=True)
    skill_tags = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    uploaded_by = Column(String(64), nullable=True)
    source = Column(String(64), nullable=False, default="WEB_DEMO")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    candidate = relationship("Candidate", back_populates="resume_files")
    screening_reports = relationship("ResumeScreeningReport", back_populates="resume_file")


class ResumeScreeningReport(Base):
    __tablename__ = "resume_screening_reports"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    candidate_id = Column(BigInteger, ForeignKey("candidates.id"), nullable=False, index=True)
    resume_file_id = Column(BigInteger, ForeignKey("resume_files.id"), nullable=False, index=True)
    position_name = Column(String(128), nullable=True, index=True)
    job_requirements = Column(Text, nullable=True)
    match_score = Column(Float, nullable=False, default=0)
    match_level = Column(String(32), nullable=True)
    match_reason = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)
    risks = Column(JSON, nullable=True)
    missing_requirements = Column(JSON, nullable=True)
    suggested_interview_questions = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    candidate = relationship("Candidate", back_populates="screening_reports")
    resume_file = relationship("ResumeFile", back_populates="screening_reports")


Index("idx_candidates_name_position", Candidate.name, Candidate.position_name)
