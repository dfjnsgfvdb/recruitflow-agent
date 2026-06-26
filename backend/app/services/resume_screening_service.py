import json
import re
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models
from app.llm.openai_compatible_provider import OpenAICompatibleProvider
from app.schemas.resume import ResumeParseResult


SCREENING_SCHEMA = {
    "name": "resume_screening_report",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["match_score", "match_level", "match_reason", "strengths", "risks", "missing_requirements", "suggested_interview_questions"],
        "properties": {
            "match_score": {"type": "number", "minimum": 0, "maximum": 100},
            "match_level": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW", "UNKNOWN"]},
            "match_reason": {"type": "string"},
            "strengths": {"type": "array", "items": {"type": "string"}},
            "risks": {"type": "array", "items": {"type": "string"}},
            "missing_requirements": {"type": "array", "items": {"type": "string"}},
            "suggested_interview_questions": {"type": "array", "items": {"type": "string"}},
        },
    },
    "strict": True,
}


def generate_screening_report(
    db: Session,
    candidate: models.Candidate,
    resume_file: models.ResumeFile,
    resume_parse_result: ResumeParseResult,
    position_name: Optional[str],
    job_requirements: Optional[str] = None,
) -> models.ResumeScreeningReport:
    """生成岗位匹配报告。真实模型可用时优先使用，失败时回退规则评分。"""
    report_data = None
    if job_requirements:
        report_data = _try_llm_screening(resume_parse_result, position_name, job_requirements)
    if not report_data:
        report_data = _rule_based_screening(resume_parse_result, position_name, job_requirements)

    report = models.ResumeScreeningReport(
        candidate_id=candidate.id,
        resume_file_id=resume_file.id,
        position_name=position_name or candidate.position_name,
        job_requirements=job_requirements,
        match_score=report_data["match_score"],
        match_level=report_data["match_level"],
        match_reason=report_data["match_reason"],
        strengths=report_data.get("strengths") or [],
        risks=report_data.get("risks") or [],
        missing_requirements=report_data.get("missing_requirements") or [],
        suggested_interview_questions=report_data.get("suggested_interview_questions") or [],
    )
    db.add(report)
    candidate.match_score = report.match_score
    candidate.match_level = report.match_level
    db.commit()
    db.refresh(report)
    db.refresh(candidate)
    return report


def _try_llm_screening(
    resume_parse_result: ResumeParseResult,
    position_name: Optional[str],
    job_requirements: str,
) -> Optional[Dict[str, Any]]:
    provider_name = (settings.llm_provider or "mock").strip().lower()
    if provider_name == "mock" or provider_name not in {"openai", "qwen", "deepseek"}:
        return None
    if not settings.llm_api_key or not settings.llm_model:
        return None
    try:
        provider = OpenAICompatibleProvider(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            timeout_seconds=settings.llm_timeout_seconds,
        )
        user_prompt = f"""
岗位名称：{position_name or '未提供'}
岗位要求：{job_requirements}
简历结构化结果：{json.dumps(resume_parse_result.model_dump(mode='json'), ensure_ascii=False)}

请只根据简历和岗位要求生成匹配报告。不要使用性别、民族、婚姻、政治面貌、身份证号、健康信息作为评分依据。
""".strip()
        return provider.generate_json(
            system_prompt="你是招聘简历筛选助手，只输出 JSON。",
            user_prompt=user_prompt,
            json_schema=SCREENING_SCHEMA,
        )
    except Exception:
        return None


def _rule_based_screening(
    resume_parse_result: ResumeParseResult,
    position_name: Optional[str],
    job_requirements: Optional[str],
) -> Dict[str, Any]:
    skills = resume_parse_result.skills or []
    text = " ".join(skills + [resume_parse_result.resume_summary or "", position_name or ""])
    requirements = _extract_requirement_keywords(job_requirements or position_name or "")

    if requirements:
        matched = [item for item in requirements if item.lower() in text.lower()]
        missing = [item for item in requirements if item not in matched]
        score = round(len(matched) / max(len(requirements), 1) * 100, 2)
        reason = f"规则匹配：命中 {len(matched)}/{len(requirements)} 个岗位关键词。"
    else:
        matched = skills[:6]
        missing = []
        score = min(75, 35 + len(skills) * 8) if skills else 0
        reason = "未提供明确岗位要求，按岗位名称和技能标签进行保守评分。"

    level = _level(score)
    questions = resume_parse_result.suggested_interview_questions or ["请候选人说明最相关项目的职责、技术难点和结果。"]
    return {
        "match_score": score,
        "match_level": level,
        "match_reason": reason,
        "strengths": resume_parse_result.strengths or (["匹配技能：" + "、".join(matched)] if matched else []),
        "risks": resume_parse_result.risks or ([] if score >= 60 else ["简历与岗位要求匹配信息不足"]),
        "missing_requirements": missing,
        "suggested_interview_questions": questions,
    }


def _extract_requirement_keywords(text: str) -> List[str]:
    known = ["Python", "FastAPI", "RAG", "Agent", "MySQL", "Redis", "Docker", "Java", "Spring Boot", "React", "Vue", "SQLAlchemy"]
    keywords = [item for item in known if item.lower() in text.lower()]
    if keywords:
        return keywords
    return [item for item in re.split(r"[、,，/\s]+", text) if len(item) >= 2][:10]


def _level(score: float) -> str:
    if score >= 80:
        return "HIGH"
    if score >= 60:
        return "MEDIUM"
    if score > 0:
        return "LOW"
    return "UNKNOWN"
