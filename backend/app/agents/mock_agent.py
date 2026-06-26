import re
from typing import List, Optional

from app.agents.base import BaseRecruitmentAgent
from app.schemas.agent import (
    AgentAction,
    AgentCandidateInfo,
    AgentInterviewInfo,
    AgentResult,
    AgentStageChange,
)


class MockRecruitmentAgent(BaseRecruitmentAgent):
    """基于规则的招聘 Agent，用于无 API Key 时跑通完整招聘流程。"""

    NAME_PATTERN = re.compile(r"(张三|李四|王五|赵六|钱七|孙八|周九|吴十)")
    PHONE_PATTERN = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")
    EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    POSITION_PATTERN = re.compile(r"(AI\s*Agent开发实习生|Java后端开发实习生|后端开发|Python后端开发|算法工程师|产品经理)")
    INTERVIEWER_PATTERN = re.compile(r"面试官[:：]?\s*([\u4e00-\u9fa5A-Za-z0-9_]{2,12})")
    TIME_PATTERN = re.compile(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?)")

    def parse_message(self, message: str) -> AgentResult:
        candidate = self._extract_candidate(message)
        interview = self._extract_interview(message)
        intent = self._detect_intent(message)
        confidence = 0.78 if intent != "UNKNOWN" else 0.3

        if self._needs_clarification(message, intent, candidate, interview):
            return AgentResult(
                intent=intent,
                confidence=0.45,
                candidate=candidate,
                interview=interview,
                actions=[],
                need_clarification=True,
                clarification_questions=self._clarification_questions(intent, candidate, interview),
            )

        stage_change = self._stage_change_for_intent(intent, interview)
        actions = self._actions_for_intent(intent, candidate, interview, stage_change)
        return AgentResult(
            intent=intent,
            confidence=confidence,
            candidate=candidate,
            stage_change=stage_change,
            interview=interview,
            actions=actions,
            need_clarification=False,
            clarification_questions=[],
        )

    def _detect_intent(self, message: str) -> str:
        if ("安排" in message) and any(keyword in message for keyword in ["一面", "二面", "面试"]):
            return "SCHEDULE_INTERVIEW"
        if any(keyword in message for keyword in ["淘汰", "不合适", "流程结束"]):
            return "REJECT_CANDIDATE"
        if "通过" in message and not any(keyword in message for keyword in ["投递", "简历通过"]):
            return "UPDATE_STAGE"
        if any(keyword in message for keyword in ["进展", "怎么样", "看板"]):
            return "QUERY_PROGRESS"
        if any(keyword in message for keyword in ["张三", "候选人"]) and any(keyword in message for keyword in ["投递", "简历通过"]):
            return "CREATE_CANDIDATE"
        return "UNKNOWN"

    def _extract_candidate(self, message: str) -> AgentCandidateInfo:
        name = self._first_match(self.NAME_PATTERN, message)
        phone = self._first_match(self.PHONE_PATTERN, message)
        email = self._first_match(self.EMAIL_PATTERN, message)
        position_name = self._first_match(self.POSITION_PATTERN, message)
        return AgentCandidateInfo(
            name=name,
            phone=phone,
            email=email,
            position_name=position_name,
            source=self._extract_source(message),
            education=self._extract_education(message),
            school=self._extract_school(message),
            experience_summary=message if any(k in message for k in ["经验", "项目", "实习"]) else None,
        )

    def _extract_interview(self, message: str) -> AgentInterviewInfo:
        round_value = None
        if "一面" in message:
            round_value = "FIRST"
        elif "二面" in message:
            round_value = "SECOND"
        elif "HR面" in message or "hr面" in message.lower():
            round_value = "HR"
        elif "终面" in message:
            round_value = "FINAL"

        return AgentInterviewInfo(
            round=round_value,
            interview_time=self._first_match(self.TIME_PATTERN, message),
            interviewer=self._first_match(self.INTERVIEWER_PATTERN, message),
            location=self._extract_location(message),
            result="PENDING",
        )

    def _stage_change_for_intent(self, intent: str, interview: AgentInterviewInfo) -> Optional[AgentStageChange]:
        if intent == "CREATE_CANDIDATE":
            return AgentStageChange(new_stage="RESUME_PASSED", reason="收到投递或简历通过消息")
        if intent == "SCHEDULE_INTERVIEW":
            new_stage = "INTERVIEW_PENDING"
            if interview.round == "FIRST":
                new_stage = "FIRST_INTERVIEW_PENDING"
            elif interview.round == "SECOND":
                new_stage = "SECOND_INTERVIEW_PENDING"
            elif interview.round == "HR":
                new_stage = "HR_INTERVIEW_PENDING"
            elif interview.round == "FINAL":
                new_stage = "FINAL_INTERVIEW_PENDING"
            return AgentStageChange(new_stage=new_stage, reason="HR 安排面试")
        if intent == "UPDATE_STAGE":
            return AgentStageChange(new_stage="INTERVIEW_PASSED", reason="消息中包含通过")
        if intent == "REJECT_CANDIDATE":
            return AgentStageChange(new_stage="REJECTED", reason="消息中包含淘汰、不合适或流程结束")
        return None

    def _actions_for_intent(
        self,
        intent: str,
        candidate: AgentCandidateInfo,
        interview: AgentInterviewInfo,
        stage_change: Optional[AgentStageChange],
    ) -> List[AgentAction]:
        if intent == "CREATE_CANDIDATE":
            return [AgentAction(tool="create_or_update_candidate", args=candidate.model_dump(exclude_none=True), risk_level="LOW")]
        if intent == "SCHEDULE_INTERVIEW":
            return [
                AgentAction(tool="create_or_update_candidate", args=candidate.model_dump(exclude_none=True), risk_level="LOW"),
                AgentAction(tool="create_interview", args=interview.model_dump(exclude_none=True), risk_level="MEDIUM"),
            ]
        if intent == "UPDATE_STAGE" and stage_change:
            return [AgentAction(tool="update_candidate_stage", args=stage_change.model_dump(exclude_none=True), risk_level="MEDIUM")]
        if intent == "REJECT_CANDIDATE" and stage_change:
            return [AgentAction(tool="reject_candidate", args=stage_change.model_dump(exclude_none=True), risk_level="HIGH")]
        if intent == "QUERY_PROGRESS":
            return [AgentAction(tool="get_dashboard_summary", args={}, risk_level="LOW")]
        return []

    def _needs_clarification(
        self,
        message: str,
        intent: str,
        candidate: AgentCandidateInfo,
        interview: AgentInterviewInfo,
    ) -> bool:
        # 典型不完整表达：只有候选人和“下午面试”，缺少岗位、轮次、具体时间、面试官等关键字段。
        if "李四下午面试" in message or message.strip() == "李四下午面试。":
            return True
        if intent in {"CREATE_CANDIDATE", "SCHEDULE_INTERVIEW", "UPDATE_STAGE", "REJECT_CANDIDATE"} and not candidate.name:
            return True
        if intent == "CREATE_CANDIDATE" and not candidate.position_name:
            return True
        if intent == "SCHEDULE_INTERVIEW" and (not interview.round or not interview.interview_time):
            return True
        return intent == "UNKNOWN"

    def _clarification_questions(
        self,
        intent: str,
        candidate: AgentCandidateInfo,
        interview: AgentInterviewInfo,
    ) -> List[str]:
        questions: List[str] = []
        if not candidate.name:
            questions.append("请补充候选人姓名。")
        if intent == "CREATE_CANDIDATE" and not candidate.position_name:
            questions.append("请补充候选人投递的岗位名称。")
        if intent == "SCHEDULE_INTERVIEW":
            if not interview.round:
                questions.append("请说明面试轮次，例如一面、二面或 HR 面。")
            if not interview.interview_time:
                questions.append("请补充明确的面试时间，例如 2026-06-26 14:00。")
        if not questions:
            questions.append("当前消息信息不足，请补充候选人、岗位或要执行的招聘动作。")
        return questions

    def _extract_source(self, message: str) -> Optional[str]:
        for source in ["Boss直聘", "内推", "猎头", "官网"]:
            if source in message:
                return source
        return None

    def _extract_education(self, message: str) -> Optional[str]:
        for education in ["本科", "硕士", "博士", "大专"]:
            if education in message:
                return education
        return None

    def _extract_school(self, message: str) -> Optional[str]:
        match = re.search(r"([\u4e00-\u9fa5]{2,20}大学|[\u4e00-\u9fa5]{2,20}学院)", message)
        return match.group(1) if match else None

    def _extract_location(self, message: str) -> Optional[str]:
        match = re.search(r"(?:地点|会议室|地址)[:：]?\s*([\u4e00-\u9fa5A-Za-z0-9_\-]+)", message)
        if match:
            return match.group(1)
        if "腾讯会议" in message:
            return "腾讯会议"
        return None

    def _first_match(self, pattern: re.Pattern, message: str) -> Optional[str]:
        match = pattern.search(message)
        return match.group(1) if match else None
