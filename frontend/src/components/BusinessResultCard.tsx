import { Card, Descriptions, Tag } from 'antd';
import MatchScore from './MatchScore';
import ResumeStatusTag from './ResumeStatusTag';
import SourceTag from './SourceTag';
import StageTag from './StageTag';
import type { AgentProcessResponse } from '../types/agent';
import type { ResumeUploadResponse } from '../types/resume';

interface BusinessResultCardProps {
  agentResult?: AgentProcessResponse | null;
  resumeResult?: ResumeUploadResponse | null;
}

export default function BusinessResultCard({ agentResult, resumeResult }: BusinessResultCardProps) {
  const agentCandidate = agentResult?.agent_result.candidate;
  const resumeCandidate = resumeResult?.candidate;
  const candidate = resumeCandidate || agentCandidate || {};
  const interview = agentResult?.agent_result.interview || {};
  const pendingAction = agentResult?.executed_actions.find((item) => item.need_confirmation);
  const stage = resumeCandidate?.stage || agentResult?.agent_result.stage_change?.new_stage;
  const source = resumeCandidate?.source || agentCandidate?.source;

  return (
    <Card size="small" title="业务结果摘要" className="business-result-card">
      <Descriptions size="small" column={2}>
        <Descriptions.Item label="候选人姓名">{candidate.name || '未识别'}</Descriptions.Item>
        <Descriptions.Item label="应聘岗位">{candidate.position_name || '未识别'}</Descriptions.Item>
        <Descriptions.Item label="当前阶段">
          <StageTag stage={stage || undefined} />
        </Descriptions.Item>
        <Descriptions.Item label="消息来源">
          <SourceTag source={source || undefined} />
        </Descriptions.Item>
        <Descriptions.Item label="面试时间">{interview.interview_time || '未识别'}</Descriptions.Item>
        <Descriptions.Item label="面试官">{interview.interviewer || '未识别'}</Descriptions.Item>
        <Descriptions.Item label="是否需要追问">
          <Tag color={agentResult?.need_clarification ? 'orange' : 'green'}>
            {agentResult?.need_clarification ? '需要追问' : '无需追问'}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="待确认动作">
          <Tag color={pendingAction ? 'red' : 'green'}>
            {pendingAction ? `已生成 #${pendingAction.pending_action_id}` : '无'}
          </Tag>
        </Descriptions.Item>
        {resumeResult?.resume_file ? (
          <>
            <Descriptions.Item label="简历解析状态">
              <ResumeStatusTag status={resumeResult.resume_file.parse_status} />
            </Descriptions.Item>
            <Descriptions.Item label="岗位匹配分">
              <MatchScore score={resumeResult.screening_report?.match_score || resumeResult.candidate?.match_score} size="small" />
            </Descriptions.Item>
          </>
        ) : null}
      </Descriptions>
    </Card>
  );
}
