from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentMessageRequest(BaseModel):
    message: str
    sender: Optional[str] = "HR小王"
    source: Optional[str] = "WEB_DEMO"


class AgentAction(BaseModel):
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "LOW"


class AgentCandidateInfo(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    position_name: Optional[str] = None
    source: Optional[str] = None
    education: Optional[str] = None
    school: Optional[str] = None
    experience_summary: Optional[str] = None
    owner: Optional[str] = None


class AgentStageChange(BaseModel):
    old_stage: Optional[str] = None
    new_stage: Optional[str] = None
    reason: Optional[str] = None


class AgentInterviewInfo(BaseModel):
    round: Optional[str] = None
    interview_time: Optional[str] = None
    interviewer: Optional[str] = None
    location: Optional[str] = None
    result: Optional[str] = "PENDING"
    feedback: Optional[str] = None


class AgentQueryInfo(BaseModel):
    position_name: Optional[str] = None
    time_range: Optional[str] = None
    metric: Optional[str] = None


class AgentResult(BaseModel):
    intent: str
    confidence: float = 0
    candidate: AgentCandidateInfo = Field(default_factory=AgentCandidateInfo)
    stage_change: AgentStageChange = Field(default_factory=AgentStageChange)
    interview: AgentInterviewInfo = Field(default_factory=AgentInterviewInfo)
    query: AgentQueryInfo = Field(default_factory=AgentQueryInfo)
    actions: List[AgentAction] = Field(default_factory=list)
    need_clarification: bool = False
    clarification_questions: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AgentProcessResponse(BaseModel):
    success: bool
    need_clarification: bool
    message: str
    agent_result: AgentResult
    executed_actions: List[Dict[str, Any]] = Field(default_factory=list)


class BatchAgentMessageRequest(BaseModel):
    raw_text: str
    source: str = "WECOM_GROUP"
    default_sender: str = "HR小王"


class BatchAgentMessageItemResult(BaseModel):
    index: int
    sender: str
    message: str
    success: bool
    need_clarification: bool
    need_confirmation: bool
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class BatchAgentMessageResponse(BaseModel):
    success: bool
    total: int
    success_count: int
    need_clarification_count: int
    need_confirmation_count: int
    failed_count: int
    items: List[BatchAgentMessageItemResult]
