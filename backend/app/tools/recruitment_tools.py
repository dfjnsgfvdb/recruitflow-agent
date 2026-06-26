from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.constants import EventStatus, PendingActionStatus, RiskLevel, ToolName
from app.core.state_machine import check_stage_transition, infer_stage_from_interview_round
from app.db import models
from app.schemas.agent import AgentCandidateInfo, AgentResult
from app.services import candidate_service, confirmation_service, dashboard_service, event_service, interview_service
from app.services.stage_service import update_candidate_stage_with_check
from app.tools import tencent_doc_mock, wecom_mock
from app.tools.risk_policy import get_tool_risk_level
from app.tools.tool_result import ToolExecutionResult


class RecruitmentToolExecutor:
    """执行 Agent actions 的安全网关。

    LLM 只负责结构化抽取，不能直接写数据库。这里统一做字段完整性校验、状态机校验、
    风险等级判断和高风险确认，避免模型误判导致淘汰、Offer、入职等高风险动作直接落库。
    """

    def execute(self, db: Session, agent_result: AgentResult, raw_text: str, sender: str, source: str) -> Dict[str, Any]:
        executed_results: List[ToolExecutionResult] = []
        extracted_json = agent_result.model_dump(mode="json")

        if agent_result.need_clarification:
            result = ToolExecutionResult(
                tool=ToolName.ASK_CLARIFICATION,
                success=True,
                status=EventStatus.NEED_CLARIFICATION,
                message="需要补充信息：" + "；".join(agent_result.clarification_questions),
                data={"clarification_questions": agent_result.clarification_questions},
                risk_level=RiskLevel.LOW,
            )
            executed_results.append(result)
            self._write_event(
                db=db,
                raw_text=raw_text,
                agent_result=agent_result,
                status=EventStatus.NEED_CLARIFICATION,
                sender=sender,
                source=source,
                action_summary=result.message,
            )
            return self._build_response(agent_result, executed_results, result.message)

        try:
            intent = agent_result.intent
            if intent == "CREATE_CANDIDATE":
                executed_results.extend(self._execute_create_candidate(db, agent_result, raw_text, sender, source))
            elif intent == "SCHEDULE_INTERVIEW":
                executed_results.append(self._execute_schedule_interview(db, agent_result, raw_text, sender, source))
            elif intent == "UPDATE_STAGE":
                executed_results.append(self._execute_update_stage(db, agent_result, raw_text, sender, source))
            elif intent == "REJECT_CANDIDATE":
                executed_results.append(
                    self._create_confirmation_for_agent_action(
                        db=db,
                        agent_result=agent_result,
                        raw_text=raw_text,
                        sender=sender,
                        source=source,
                        action_type=ToolName.REJECT_CANDIDATE,
                        reason="淘汰候选人属于高风险动作，需要 HR 确认。",
                    )
                )
            elif intent == "QUERY_PROGRESS":
                executed_results.append(self._execute_query_dashboard(db, agent_result, raw_text, sender, source))
            else:
                executed_results.extend(self._execute_actions_by_model_output(db, agent_result, raw_text, sender, source))

            message = self._summary_message(executed_results)
            return self._build_response(agent_result, executed_results, message)
        except Exception as exc:
            db.rollback()
            failed_result = ToolExecutionResult(
                tool="execute_agent_actions",
                success=False,
                status=EventStatus.FAILED,
                message="执行 Agent actions 失败。",
                risk_level=RiskLevel.HIGH,
                error_message=str(exc),
            )
            executed_results.append(failed_result)
            self._write_event(
                db=db,
                raw_text=raw_text,
                agent_result=agent_result,
                status=EventStatus.FAILED,
                sender=sender,
                source=source,
                action_summary=failed_result.message,
                error_message=str(exc),
            )
            return self._build_response(agent_result, executed_results, f"执行失败：{exc}", success=False)

    def execute_confirmed_action(
        self,
        db: Session,
        pending_action: models.PendingAction,
        approved_by: str,
    ) -> ToolExecutionResult:
        if pending_action.status not in {PendingActionStatus.PENDING, PendingActionStatus.APPROVED}:
            return ToolExecutionResult(
                tool=pending_action.action_type,
                success=False,
                status=EventStatus.FAILED,
                message="该待确认动作已处理，不能重复执行。",
                risk_level=pending_action.risk_level,
                error_message="Pending action status is not executable.",
            )

        try:
            payload = pending_action.payload or {}
            candidate = self._get_candidate_for_pending_action(db, pending_action, payload)
            if not candidate:
                raise ValueError("待确认动作缺少可执行的候选人。")

            action_type = self._normalize_tool_name(pending_action.action_type)
            target_stage = self._target_stage_for_confirmed_action(action_type, payload)

            if action_type == ToolName.CREATE_INTERVIEW:
                interview_info = payload.get("interview") or {}
                target_stage = target_stage or infer_stage_from_interview_round(interview_info.get("round"))
                if target_stage:
                    candidate.stage = target_stage
                    candidate.last_followup_at = datetime.now()
                interview = interview_service.create_interview(db, candidate.id, interview_info)
                data = {"candidate_id": candidate.id, "interview_id": interview.id, "stage": candidate.stage}
                message = "HR 已确认，面试安排已执行。"
            elif action_type in {
                ToolName.REJECT_CANDIDATE,
                ToolName.SEND_OFFER,
                ToolName.MARK_HIRED,
                ToolName.UPDATE_CANDIDATE_STAGE,
            }:
                if not target_stage:
                    raise ValueError("待确认动作缺少目标阶段。")
                check_result = check_stage_transition(candidate.stage, target_stage)
                candidate.stage = target_stage
                candidate.last_followup_at = datetime.now()
                db.commit()
                db.refresh(candidate)
                data = {
                    "candidate_id": candidate.id,
                    "stage": candidate.stage,
                    "confirmed_execution": True,
                    "state_machine_reason": check_result.reason,
                }
                message = "HR 已确认，高风险或异常状态流转已执行。"
            else:
                raise ValueError(f"不支持确认执行的动作类型：{pending_action.action_type}")

            confirmation_service.mark_action_executed(db, pending_action.id)
            self._write_event(
                db=db,
                raw_text=f"Confirmed pending action {pending_action.id}",
                intent=action_type,
                extracted_json=payload,
                confidence=1,
                status=EventStatus.SUCCESS,
                sender=approved_by,
                source="CONFIRMATION",
                candidate_id=candidate.id,
                action_summary=message,
            )
            return ToolExecutionResult(
                tool=action_type,
                success=True,
                status=EventStatus.SUCCESS,
                message=message,
                data=data,
                risk_level=pending_action.risk_level,
            )
        except Exception as exc:
            db.rollback()
            confirmation_service.mark_action_failed(db, pending_action.id, str(exc))
            self._write_event(
                db=db,
                raw_text=f"Confirmed pending action {pending_action.id}",
                intent=pending_action.action_type,
                extracted_json=pending_action.payload,
                confidence=1,
                status=EventStatus.FAILED,
                sender=approved_by,
                source="CONFIRMATION",
                candidate_id=pending_action.candidate_id,
                action_summary="待确认动作执行失败。",
                error_message=str(exc),
            )
            return ToolExecutionResult(
                tool=pending_action.action_type,
                success=False,
                status=EventStatus.FAILED,
                message="待确认动作执行失败。",
                risk_level=pending_action.risk_level,
                error_message=str(exc),
            )

    def _execute_create_candidate(
        self,
        db: Session,
        agent_result: AgentResult,
        raw_text: str,
        sender: str,
        source: str,
    ) -> List[ToolExecutionResult]:
        results: List[ToolExecutionResult] = []
        candidate = candidate_service.create_or_update_candidate(
            db,
            agent_result.candidate or AgentCandidateInfo(),
            stage=self._stage_from_result(agent_result) or "NEW",
        )
        result = ToolExecutionResult(
            tool=ToolName.CREATE_CANDIDATE,
            success=True,
            status=EventStatus.SUCCESS,
            message=f"已创建或更新候选人 {candidate.name}。",
            data={"candidate_id": candidate.id, "stage": candidate.stage},
            risk_level=RiskLevel.LOW,
        )
        results.append(result)
        self._write_event_for_result(db, raw_text, agent_result, result, sender, source, candidate.id)
        results.append(self._safe_sync_candidate(db, raw_text, agent_result, sender, source, candidate))
        results.append(self._safe_send_notice(db, raw_text, agent_result, sender, source, candidate))
        return results

    def _execute_schedule_interview(
        self,
        db: Session,
        agent_result: AgentResult,
        raw_text: str,
        sender: str,
        source: str,
    ) -> ToolExecutionResult:
        candidate = candidate_service.create_or_update_candidate(db, agent_result.candidate or AgentCandidateInfo())
        target_stage = infer_stage_from_interview_round(agent_result.interview.round)
        if not target_stage:
            return self._create_pending_action(
                db=db,
                agent_result=agent_result,
                raw_text=raw_text,
                sender=sender,
                source=source,
                candidate_id=candidate.id,
                action_type=ToolName.CREATE_INTERVIEW,
                risk_level=RiskLevel.MEDIUM,
                reason="面试轮次无法安全推断目标阶段，需要 HR 确认。",
                payload=self._pending_payload(agent_result, raw_text, source, target_stage=target_stage),
            )

        check_result = check_stage_transition(candidate.stage, target_stage)
        if check_result.need_confirmation or not check_result.allowed:
            return self._create_pending_action(
                db=db,
                agent_result=agent_result,
                raw_text=raw_text,
                sender=sender,
                source=source,
                candidate_id=candidate.id,
                action_type=ToolName.CREATE_INTERVIEW,
                risk_level=RiskLevel.MEDIUM,
                reason=check_result.reason,
                payload=self._pending_payload(agent_result, raw_text, source, target_stage=target_stage),
            )

        stage_result = update_candidate_stage_with_check(db, candidate, target_stage, "安排面试前更新候选人阶段。")
        if not stage_result.success:
            return stage_result
        interview = interview_service.create_interview(db, candidate.id, agent_result.interview)
        result = ToolExecutionResult(
            tool=ToolName.CREATE_INTERVIEW,
            success=True,
            status=EventStatus.SUCCESS,
            message=f"已为候选人 {candidate.name} 安排面试。",
            data={"candidate_id": candidate.id, "interview_id": interview.id, "stage": candidate.stage},
            risk_level=RiskLevel.MEDIUM,
        )
        self._write_event_for_result(db, raw_text, agent_result, result, sender, source, candidate.id)
        return result

    def _execute_update_stage(
        self,
        db: Session,
        agent_result: AgentResult,
        raw_text: str,
        sender: str,
        source: str,
    ) -> ToolExecutionResult:
        candidate = self._find_or_create_candidate(db, agent_result)
        target_stage = self._stage_from_result(agent_result)
        stage_result = update_candidate_stage_with_check(db, candidate, target_stage, agent_result.stage_change.reason)
        if stage_result.need_confirmation:
            return self._create_pending_action(
                db=db,
                agent_result=agent_result,
                raw_text=raw_text,
                sender=sender,
                source=source,
                candidate_id=candidate.id,
                action_type=ToolName.UPDATE_CANDIDATE_STAGE,
                risk_level=RiskLevel.MEDIUM,
                reason=stage_result.message,
                payload=self._pending_payload(agent_result, raw_text, source, target_stage=target_stage),
            )
        self._write_event_for_result(db, raw_text, agent_result, stage_result, sender, source, candidate.id)
        return stage_result

    def _execute_query_dashboard(
        self,
        db: Session,
        agent_result: AgentResult,
        raw_text: str,
        sender: str,
        source: str,
    ) -> ToolExecutionResult:
        dashboard = dashboard_service.get_dashboard_summary(db)
        result = ToolExecutionResult(
            tool=ToolName.QUERY_DASHBOARD,
            success=True,
            status=EventStatus.SUCCESS,
            message="已返回招聘看板摘要。",
            data=dashboard.model_dump(mode="json"),
            risk_level=RiskLevel.LOW,
        )
        self._write_event_for_result(db, raw_text, agent_result, result, sender, source, None)
        return result

    def _execute_actions_by_model_output(
        self,
        db: Session,
        agent_result: AgentResult,
        raw_text: str,
        sender: str,
        source: str,
    ) -> List[ToolExecutionResult]:
        results: List[ToolExecutionResult] = []
        for action in agent_result.actions:
            tool_name = self._normalize_tool_name(action.tool)
            risk_level = get_tool_risk_level(tool_name, action.risk_level)
            if risk_level == RiskLevel.HIGH:
                results.append(
                    self._create_confirmation_for_agent_action(
                        db=db,
                        agent_result=agent_result,
                        raw_text=raw_text,
                        sender=sender,
                        source=source,
                        action_type=tool_name,
                        reason="模型输出了高风险动作，需要 HR 确认。",
                    )
                )
            elif tool_name in {ToolName.QUERY_DASHBOARD, "get_dashboard_summary"}:
                results.append(self._execute_query_dashboard(db, agent_result, raw_text, sender, source))
            else:
                results.append(
                    ToolExecutionResult(
                        tool=tool_name,
                        success=False,
                        status=EventStatus.FAILED,
                        message=f"暂不支持自动执行该工具：{tool_name}",
                        risk_level=risk_level,
                        error_message="Unsupported tool.",
                    )
                )
        if not results:
            result = ToolExecutionResult(
                tool="unknown",
                success=False,
                status=EventStatus.FAILED,
                message="无法识别招聘意图或工具动作。",
                risk_level=RiskLevel.HIGH,
                error_message="No executable actions.",
            )
            self._write_event_for_result(db, raw_text, agent_result, result, sender, source, None)
            results.append(result)
        return results

    def _create_confirmation_for_agent_action(
        self,
        db: Session,
        agent_result: AgentResult,
        raw_text: str,
        sender: str,
        source: str,
        action_type: str,
        reason: str,
    ) -> ToolExecutionResult:
        candidate = self._find_or_create_candidate(db, agent_result)
        return self._create_pending_action(
            db=db,
            agent_result=agent_result,
            raw_text=raw_text,
            sender=sender,
            source=source,
            candidate_id=candidate.id if candidate else None,
            action_type=action_type,
            risk_level=get_tool_risk_level(action_type),
            reason=reason,
            payload=self._pending_payload(agent_result, raw_text, source, target_stage=self._target_stage_for_action(action_type, agent_result)),
        )

    def _create_pending_action(
        self,
        db: Session,
        agent_result: AgentResult,
        raw_text: str,
        sender: str,
        source: str,
        candidate_id: Optional[int],
        action_type: str,
        risk_level: str,
        reason: str,
        payload: Dict[str, Any],
    ) -> ToolExecutionResult:
        pending_action = confirmation_service.create_pending_action(
            db=db,
            candidate_id=candidate_id,
            action_type=action_type,
            risk_level=risk_level,
            payload=payload,
            reason=reason,
            requested_by=sender,
        )
        result = ToolExecutionResult(
            tool=action_type,
            success=True,
            status=EventStatus.NEED_CONFIRMATION,
            message="已生成待确认任务。",
            data={"candidate_id": candidate_id},
            risk_level=risk_level,
            need_confirmation=True,
            pending_action_id=pending_action.id,
        )
        self._write_event_for_result(db, raw_text, agent_result, result, sender, source, candidate_id)
        return result

    def _find_or_create_candidate(self, db: Session, agent_result: AgentResult):
        info = agent_result.candidate or AgentCandidateInfo()
        candidate = candidate_service.find_candidate(
            db,
            name=info.name,
            phone=info.phone,
            email=info.email,
            position_name=info.position_name,
        )
        if candidate:
            return candidate
        return candidate_service.create_or_update_candidate(db, info)

    def _safe_sync_candidate(
        self,
        db: Session,
        raw_text: str,
        agent_result: AgentResult,
        sender: str,
        source: str,
        candidate: models.Candidate,
    ) -> ToolExecutionResult:
        try:
            sync_result = tencent_doc_mock.sync_candidate(candidate)
            self._create_sync_log(db, sync_result, operation=sync_result.get("operation", "UPSERT_CANDIDATE"))
            result = ToolExecutionResult(
                tool=ToolName.SYNC_TO_TENCENT_DOC,
                success=True,
                status=EventStatus.SUCCESS,
                message="已同步候选人到腾讯文档 Mock。",
                data=sync_result,
                risk_level=RiskLevel.LOW,
            )
        except Exception as exc:
            self._create_sync_log(
                db,
                {"target": "TENCENT_DOC", "status": EventStatus.FAILED, "error_message": str(exc)},
                operation="UPSERT_CANDIDATE",
                error_message=str(exc),
            )
            result = ToolExecutionResult(
                tool=ToolName.SYNC_TO_TENCENT_DOC,
                success=False,
                status=EventStatus.FAILED,
                message="同步腾讯文档 Mock 失败，但不影响主流程。",
                risk_level=RiskLevel.LOW,
                error_message=str(exc),
            )
        self._write_event_for_result(db, raw_text, agent_result, result, sender, source, candidate.id)
        return result

    def _safe_send_notice(
        self,
        db: Session,
        raw_text: str,
        agent_result: AgentResult,
        sender: str,
        source: str,
        candidate: models.Candidate,
    ) -> ToolExecutionResult:
        try:
            notice_result = wecom_mock.send_notice(f"候选人 {candidate.name} 已进入招聘流程。")
            self._create_sync_log(db, notice_result, operation="SEND_NOTICE")
            result = ToolExecutionResult(
                tool=ToolName.SEND_WECOM_NOTICE,
                success=True,
                status=EventStatus.SUCCESS,
                message="已发送企业微信 Mock 通知。",
                data=notice_result,
                risk_level=RiskLevel.LOW,
            )
        except Exception as exc:
            self._create_sync_log(
                db,
                {"target": "WECOM", "status": EventStatus.FAILED, "error_message": str(exc)},
                operation="SEND_NOTICE",
                error_message=str(exc),
            )
            result = ToolExecutionResult(
                tool=ToolName.SEND_WECOM_NOTICE,
                success=False,
                status=EventStatus.FAILED,
                message="企业微信 Mock 通知失败，但不影响主流程。",
                risk_level=RiskLevel.LOW,
                error_message=str(exc),
            )
        self._write_event_for_result(db, raw_text, agent_result, result, sender, source, candidate.id)
        return result

    def _write_event_for_result(
        self,
        db: Session,
        raw_text: str,
        agent_result: AgentResult,
        result: ToolExecutionResult,
        sender: str,
        source: str,
        candidate_id: Optional[int],
    ) -> None:
        self._write_event(
            db=db,
            raw_text=raw_text,
            agent_result=agent_result,
            status=result.status,
            sender=sender,
            source=source,
            candidate_id=candidate_id,
            action_summary=result.message,
            error_message=result.error_message,
        )

    def _write_event(
        self,
        db: Session,
        raw_text: str,
        status: str,
        sender: str,
        source: str,
        agent_result: Optional[AgentResult] = None,
        intent: Optional[str] = None,
        extracted_json: Optional[Dict[str, Any]] = None,
        confidence: float = 0,
        candidate_id: Optional[int] = None,
        action_summary: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        event_service.create_event(
            db=db,
            raw_text=raw_text,
            intent=intent or (agent_result.intent if agent_result else "UNKNOWN"),
            extracted_json=extracted_json or (agent_result.model_dump(mode="json") if agent_result else None),
            confidence=agent_result.confidence if agent_result else confidence,
            status=status,
            sender=sender,
            source=source,
            candidate_id=candidate_id,
            action_summary=action_summary,
            error_message=error_message,
        )

    def _pending_payload(
        self,
        agent_result: AgentResult,
        raw_text: str,
        source: str,
        target_stage: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "raw_text": raw_text,
            "source": source,
            "target_stage": target_stage,
            "candidate": agent_result.candidate.model_dump(mode="json") if agent_result.candidate else None,
            "interview": agent_result.interview.model_dump(mode="json") if agent_result.interview else None,
            "stage_change": agent_result.stage_change.model_dump(mode="json") if agent_result.stage_change else None,
            "agent_result": agent_result.model_dump(mode="json"),
        }

    def _target_stage_for_action(self, action_type: str, agent_result: AgentResult) -> Optional[str]:
        if action_type == ToolName.REJECT_CANDIDATE:
            return "REJECTED"
        if action_type == ToolName.SEND_OFFER:
            return "OFFER_SENT"
        if action_type == ToolName.MARK_HIRED:
            return "HIRED"
        if action_type == ToolName.UPDATE_CANDIDATE_STAGE:
            return self._stage_from_result(agent_result)
        if action_type == ToolName.CREATE_INTERVIEW:
            return infer_stage_from_interview_round(agent_result.interview.round)
        return None

    def _target_stage_for_confirmed_action(self, action_type: str, payload: Dict[str, Any]) -> Optional[str]:
        if action_type == ToolName.REJECT_CANDIDATE:
            return "REJECTED"
        if action_type == ToolName.SEND_OFFER:
            return "OFFER_SENT"
        if action_type == ToolName.MARK_HIRED:
            return "HIRED"
        if action_type == ToolName.UPDATE_CANDIDATE_STAGE:
            stage_change = payload.get("stage_change") or {}
            return payload.get("target_stage") or stage_change.get("new_stage")
        if action_type == ToolName.CREATE_INTERVIEW:
            return payload.get("target_stage")
        return payload.get("target_stage")

    def _get_candidate_for_pending_action(
        self,
        db: Session,
        pending_action: models.PendingAction,
        payload: Dict[str, Any],
    ):
        if pending_action.candidate_id:
            return db.query(models.Candidate).filter(models.Candidate.id == pending_action.candidate_id).first()
        info = payload.get("candidate") or {}
        return candidate_service.find_candidate(
            db,
            name=info.get("name"),
            phone=info.get("phone"),
            email=info.get("email"),
            position_name=info.get("position_name"),
        )

    def _normalize_tool_name(self, tool_name: str) -> str:
        aliases = {
            "create_or_update_candidate": ToolName.CREATE_CANDIDATE,
            "get_dashboard_summary": ToolName.QUERY_DASHBOARD,
        }
        return aliases.get(tool_name, tool_name)

    def _stage_from_result(self, agent_result: AgentResult) -> Optional[str]:
        return agent_result.stage_change.new_stage if agent_result.stage_change else None

    def _create_sync_log(
        self,
        db: Session,
        result: Dict[str, Any],
        operation: str,
        error_message: Optional[str] = None,
    ) -> None:
        sync_log = models.SyncLog(
            target=result.get("target", "UNKNOWN"),
            operation=operation,
            payload=result,
            status=result.get("status", EventStatus.SUCCESS),
            error_message=error_message,
        )
        db.add(sync_log)
        db.commit()

    def _summary_message(self, results: List[ToolExecutionResult]) -> str:
        if any(result.need_confirmation for result in results):
            return "已生成待确认任务，请 HR 负责人确认后执行。"
        if all(result.success for result in results):
            return "处理完成。"
        return "部分动作执行失败，请查看 executed_actions。"

    def _build_response(
        self,
        agent_result: AgentResult,
        results: List[ToolExecutionResult],
        message: str,
        success: bool = True,
    ) -> Dict[str, Any]:
        return {
            "success": success,
            "need_clarification": agent_result.need_clarification,
            "message": message,
            "agent_result": agent_result,
            "executed_actions": [result.model_dump(mode="json") for result in results],
        }
