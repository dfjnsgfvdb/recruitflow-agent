import re
from typing import List, Optional

from app.agents.resume_json_schema import RECRUITMENT_RESUME_JSON_SCHEMA
from app.agents.resume_prompts import RECRUITMENT_RESUME_SYSTEM_PROMPT, build_resume_user_prompt
from app.core.config import settings
from app.llm.openai_compatible_provider import OpenAICompatibleProvider
from app.llm.provider import BaseLLMProvider
from app.schemas.resume import ResumeParseResult


class MockResumeAgent:
    """无 API Key 时的简历解析兜底，保证 Demo 全流程可运行。"""

    def parse_resume(self, raw_text: str) -> ResumeParseResult:
        text = raw_text or ""
        skills = self._extract_skills(text)
        name = self._extract_name(text)
        result = ResumeParseResult(
            candidate={
                "name": name,
                "phone": self._extract_phone(text),
                "email": self._extract_email(text),
                "education": self._extract_education(text),
                "school": self._extract_school(text),
                "major": self._extract_major(text),
                "graduation_year": self._extract_graduation_year(text),
                "work_years": self._extract_work_years(text),
            },
            skills=skills,
            project_experiences=self._extract_projects(text, skills),
            work_experiences=[],
            certificates=self._extract_certificates(text),
            resume_summary=self._summary(text, skills),
            strengths=self._strengths(skills),
            risks=["简历由 Mock 规则解析，建议人工复核关键字段"],
            suggested_interview_questions=self._questions(skills),
            confidence=0.68 if len(text) > 300 else 0.45,
            need_manual_review=len(text) < 300,
            warnings=[] if len(text) >= 300 else ["简历文本较短，可能需要人工复核"],
        )
        return result

    def _extract_phone(self, text: str) -> Optional[str]:
        match = re.search(r"1[3-9]\d{9}", text)
        return match.group(0) if match else None

    def _extract_email(self, text: str) -> Optional[str]:
        match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        return match.group(0) if match else None

    def _extract_name(self, text: str) -> Optional[str]:
        patterns = [r"姓名[:：\s]*([\u4e00-\u9fa5]{2,4})", r"候选人[:：\s]*([\u4e00-\u9fa5]{2,4})"]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        match = re.search(r"\b(张三|李四|王五|赵六)\b", text)
        return match.group(1) if match else None

    def _extract_education(self, text: str) -> Optional[str]:
        for item in ["博士", "硕士", "研究生", "本科", "大专"]:
            if item in text:
                return item
        return None

    def _extract_school(self, text: str) -> Optional[str]:
        match = re.search(r"([\u4e00-\u9fa5]{2,20}(?:大学|学院|学校))", text)
        return match.group(1) if match else None

    def _extract_major(self, text: str) -> Optional[str]:
        match = re.search(r"专业[:：\s]*([\u4e00-\u9fa5A-Za-z0-9 +#.-]{2,30})", text)
        return match.group(1).strip() if match else None

    def _extract_graduation_year(self, text: str) -> Optional[str]:
        match = re.search(r"(20\d{2})\s*年?\s*毕业", text)
        return match.group(1) if match else None

    def _extract_work_years(self, text: str) -> Optional[str]:
        match = re.search(r"(\d+)\s*年(?:工作|开发|后端|Python)?经验", text)
        return f"{match.group(1)}年" if match else None

    def _extract_skills(self, text: str) -> List[str]:
        known = [
            "Python",
            "FastAPI",
            "Django",
            "Flask",
            "Java",
            "Spring Boot",
            "MySQL",
            "Redis",
            "Docker",
            "Kubernetes",
            "RAG",
            "Agent",
            "LangChain",
            "Vue",
            "React",
            "TypeScript",
            "SQLAlchemy",
        ]
        lower_text = text.lower()
        skills = []
        for skill in known:
            if skill.lower() in lower_text:
                skills.append(skill)
        return skills

    def _extract_projects(self, text: str, skills: List[str]) -> List[dict]:
        if "项目" not in text and not skills:
            return []
        return [
            {
                "project_name": "简历项目经历",
                "role": None,
                "tech_stack": skills,
                "responsibilities": "从简历文本中识别到相关项目或技术经历",
                "outcomes": None,
            }
        ]

    def _extract_certificates(self, text: str) -> List[str]:
        certificates = []
        for cert in ["CET-4", "CET-6", "英语四级", "英语六级", "软考", "PMP"]:
            if cert in text:
                certificates.append(cert)
        return certificates

    def _summary(self, text: str, skills: List[str]) -> str:
        parts = []
        if skills:
            parts.append("技能标签：" + "、".join(skills[:8]))
        if text:
            parts.append(text[:180])
        return "；".join(parts) if parts else "未抽取到有效简历摘要"

    def _strengths(self, skills: List[str]) -> List[str]:
        if skills:
            return ["具备相关技术栈：" + "、".join(skills[:6])]
        return []

    def _questions(self, skills: List[str]) -> List[str]:
        if not skills:
            return ["请候选人补充最近一个项目的技术选型、个人职责和结果。"]
        return [f"请结合项目说明 {skill} 的实际使用场景和踩坑经验。" for skill in skills[:3]]


class ResumeAgent:
    def __init__(self, provider: Optional[BaseLLMProvider] = None, fallback_agent: Optional[MockResumeAgent] = None) -> None:
        self.provider = provider or self._build_provider()
        self.fallback_agent = fallback_agent or MockResumeAgent()

    def parse_resume(self, raw_text: str) -> ResumeParseResult:
        if not self.provider:
            return self.fallback_agent.parse_resume(raw_text)

        try:
            result_dict = self.provider.generate_json(
                system_prompt=RECRUITMENT_RESUME_SYSTEM_PROMPT,
                user_prompt=build_resume_user_prompt(raw_text),
                json_schema=RECRUITMENT_RESUME_JSON_SCHEMA,
            )
            return ResumeParseResult.model_validate(result_dict)
        except Exception as exc:
            if settings.llm_fallback_to_mock:
                result = self.fallback_agent.parse_resume(raw_text)
                result.need_manual_review = True
                result.warnings.append(f"真实模型解析失败，已降级 Mock：{exc}")
                return result
            return ResumeParseResult(
                resume_summary=(raw_text or "")[:500],
                confidence=0,
                need_manual_review=True,
                warnings=[f"简历模型解析失败：{exc}"],
            )

    def _build_provider(self) -> Optional[BaseLLMProvider]:
        provider_name = (settings.llm_provider or "mock").strip().lower()
        if provider_name == "mock":
            return None
        if provider_name not in {"openai", "qwen", "deepseek"}:
            return None
        if not settings.llm_api_key or not settings.llm_model:
            return None
        return OpenAICompatibleProvider(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            timeout_seconds=settings.llm_timeout_seconds,
        )
