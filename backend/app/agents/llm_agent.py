from datetime import datetime
from typing import Optional

from pydantic import ValidationError

from app.agents.base import BaseRecruitmentAgent
from app.agents.json_schema import RECRUITMENT_AGENT_JSON_SCHEMA
from app.agents.prompts import RECRUITMENT_SYSTEM_PROMPT, build_recruitment_user_prompt
from app.llm.provider import BaseLLMProvider
from app.schemas.agent import AgentResult


class LLMRecruitmentAgent(BaseRecruitmentAgent):
    def __init__(
        self,
        provider: BaseLLMProvider,
        fallback_agent: Optional[BaseRecruitmentAgent] = None,
    ) -> None:
        self.provider = provider
        self.fallback_agent = fallback_agent

    def parse_message(self, message: str) -> AgentResult:
        current_date = datetime.now().strftime("%Y-%m-%d")
        user_prompt = build_recruitment_user_prompt(message=message, current_date=current_date)

        try:
            result_dict = self.provider.generate_json(
                system_prompt=RECRUITMENT_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                json_schema=RECRUITMENT_AGENT_JSON_SCHEMA,
            )
            # Pydantic 校验是 LLM 输出进入业务流程前的边界，防止结构漂移。
            agent_result = AgentResult.model_validate(result_dict)
            return self._enforce_safety(agent_result)
        except (RuntimeError, ValidationError, ValueError, TypeError) as exc:
            if self.fallback_agent:
                return self.fallback_agent.parse_message(message)
            return AgentResult(
                intent="UNKNOWN",
                confidence=0,
                need_clarification=True,
                clarification_questions=[f"真实模型抽取失败，请补充信息或检查 LLM 配置：{exc}"],
            )

    def _enforce_safety(self, agent_result: AgentResult) -> AgentResult:
        questions = list(agent_result.clarification_questions)

        if agent_result.confidence < 0.5:
            questions.append("模型置信度较低，请 HR 确认候选人信息和招聘动作。")

        if agent_result.intent in {"CREATE_CANDIDATE", "SCHEDULE_INTERVIEW", "UPDATE_STAGE", "REJECT_CANDIDATE"}:
            if not agent_result.candidate.name:
                questions.append("请补充候选人姓名。")

        if agent_result.intent == "CREATE_CANDIDATE" and not agent_result.candidate.position_name:
            questions.append("请补充候选人投递的岗位名称。")

        if agent_result.intent == "SCHEDULE_INTERVIEW":
            if not agent_result.interview.interview_time:
                questions.append("请补充明确的面试时间。")
            if not agent_result.interview.interviewer:
                questions.append("请补充面试官。")

        deduplicated_questions = list(dict.fromkeys(questions))
        if deduplicated_questions:
            agent_result.need_clarification = True
            agent_result.clarification_questions = deduplicated_questions

        return agent_result
