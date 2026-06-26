from typing import Optional

from app.core.constants import RiskLevel, ToolName


TOOL_RISK_LEVELS = {
    ToolName.CREATE_CANDIDATE: RiskLevel.LOW,
    ToolName.SYNC_TO_TENCENT_DOC: RiskLevel.LOW,
    ToolName.SEND_WECOM_NOTICE: RiskLevel.LOW,
    ToolName.ASK_CLARIFICATION: RiskLevel.LOW,
    ToolName.QUERY_DASHBOARD: RiskLevel.LOW,
    ToolName.UPDATE_CANDIDATE_STAGE: RiskLevel.MEDIUM,
    ToolName.CREATE_INTERVIEW: RiskLevel.MEDIUM,
    ToolName.ADD_INTERVIEW_FEEDBACK: RiskLevel.MEDIUM,
    ToolName.REJECT_CANDIDATE: RiskLevel.HIGH,
    ToolName.SEND_OFFER: RiskLevel.HIGH,
    ToolName.MARK_HIRED: RiskLevel.HIGH,
    # 兼容第 3 步 Prompt / Mock Agent 中已有的工具名。
    "create_or_update_candidate": RiskLevel.LOW,
    "get_dashboard_summary": RiskLevel.LOW,
}


def get_tool_risk_level(tool_name: str, model_risk_level: Optional[str] = None) -> str:
    # 系统内置风险等级优先，不能信任模型自行声明的 LOW/MEDIUM/HIGH。
    return TOOL_RISK_LEVELS.get(tool_name, RiskLevel.HIGH)


def is_high_risk_tool(tool_name: str) -> bool:
    return get_tool_risk_level(tool_name) == RiskLevel.HIGH
