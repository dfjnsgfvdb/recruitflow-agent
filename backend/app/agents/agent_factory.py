from app.agents.base import BaseRecruitmentAgent
from app.agents.llm_agent import LLMRecruitmentAgent
from app.agents.mock_agent import MockRecruitmentAgent
from app.core.config import settings


def get_recruitment_agent() -> BaseRecruitmentAgent:
    provider_name = (settings.llm_provider or "mock").strip().lower()

    if provider_name == "mock":
        return MockRecruitmentAgent()

    if provider_name in {"openai", "qwen", "deepseek"}:
        if not settings.llm_api_key or not settings.llm_model:
            return MockRecruitmentAgent()

        fallback_agent = MockRecruitmentAgent() if settings.llm_fallback_to_mock else None
        try:
            # qwen / deepseek 暂时按 OpenAI-compatible 协议接入，base_url 全部由 .env 控制。
            from app.llm.openai_compatible_provider import OpenAICompatibleProvider

            llm_provider = OpenAICompatibleProvider(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                timeout_seconds=settings.llm_timeout_seconds,
            )
            return LLMRecruitmentAgent(provider=llm_provider, fallback_agent=fallback_agent)
        except Exception:
            if fallback_agent:
                return fallback_agent
            raise

    return MockRecruitmentAgent()
