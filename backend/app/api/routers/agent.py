import re
from typing import Dict, Tuple

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.agent_factory import get_recruitment_agent
from app.api.deps import get_db
from app.schemas.agent import (
    AgentMessageRequest,
    AgentProcessResponse,
    BatchAgentMessageItemResult,
    BatchAgentMessageRequest,
    BatchAgentMessageResponse,
)
from app.tools.recruitment_tools import RecruitmentToolExecutor

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/process-message", response_model=AgentProcessResponse)
def process_message(payload: AgentMessageRequest, db: Session = Depends(get_db)) -> AgentProcessResponse:
    agent = get_recruitment_agent()
    agent_result = agent.parse_message(payload.message)
    execution_result = RecruitmentToolExecutor().execute(
        db=db,
        agent_result=agent_result,
        raw_text=payload.message,
        sender=payload.sender or "HR小王",
        source=payload.source or "WEB_DEMO",
    )
    return AgentProcessResponse(
        success=execution_result["success"],
        need_clarification=execution_result["need_clarification"],
        message=execution_result["message"],
        agent_result=agent_result,
        executed_actions=execution_result.get("executed_actions", []),
    )


@router.post("/process-batch", response_model=BatchAgentMessageResponse)
def process_batch(payload: BatchAgentMessageRequest, db: Session = Depends(get_db)) -> BatchAgentMessageResponse:
    # 企业微信群消息通常是多行粘贴。这里逐行复用单条处理链路，单条失败不影响整体批次。
    agent = get_recruitment_agent()
    executor = RecruitmentToolExecutor()
    items = []

    lines = [line.strip() for line in payload.raw_text.splitlines() if line.strip()]
    for index, line in enumerate(lines, start=1):
        sender, message = _split_sender_and_message(line, payload.default_sender)
        try:
            agent_result = agent.parse_message(message)
            execution_result = executor.execute(
                db=db,
                agent_result=agent_result,
                raw_text=message,
                sender=sender,
                source=payload.source,
            )
            executed_actions = execution_result.get("executed_actions", [])
            need_confirmation = any(action.get("need_confirmation") for action in executed_actions)
            items.append(
                BatchAgentMessageItemResult(
                    index=index,
                    sender=sender,
                    message=message,
                    success=bool(execution_result.get("success")),
                    need_clarification=bool(execution_result.get("need_clarification")),
                    need_confirmation=need_confirmation,
                    result=_jsonable_result(execution_result),
                    error_message=None,
                )
            )
        except Exception as exc:
            items.append(
                BatchAgentMessageItemResult(
                    index=index,
                    sender=sender,
                    message=message,
                    success=False,
                    need_clarification=False,
                    need_confirmation=False,
                    result=None,
                    error_message=str(exc),
                )
            )

    return BatchAgentMessageResponse(
        success=True,
        total=len(items),
        success_count=sum(1 for item in items if item.success),
        need_clarification_count=sum(1 for item in items if item.need_clarification),
        need_confirmation_count=sum(1 for item in items if item.need_confirmation),
        failed_count=sum(1 for item in items if not item.success),
        items=items,
    )


def _split_sender_and_message(line: str, default_sender: str) -> Tuple[str, str]:
    match = re.match(r"^\s*([^:：]{1,32})\s*[:：]\s*(.+)$", line)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return default_sender, line


def _jsonable_result(result: Dict) -> Dict:
    data = dict(result)
    agent_result = data.get("agent_result")
    if hasattr(agent_result, "model_dump"):
        data["agent_result"] = agent_result.model_dump(mode="json")
    return data
