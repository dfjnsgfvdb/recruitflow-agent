import { Progress, Tooltip } from 'antd';

const stageOrder = ['NEW', 'RESUME_PASSED', 'FIRST_INTERVIEW_PENDING', 'SECOND_INTERVIEW_PENDING', 'OFFER_SENT', 'HIRED'];

const stageText: Record<string, string> = {
  NEW: '新投递',
  SCREENING: '简历筛选中',
  RESUME_PASSED: '简历通过',
  RESUME_REJECTED: '简历淘汰',
  FIRST_INTERVIEW_PENDING: '一面',
  FIRST_INTERVIEW_PASSED: '一面通过',
  FIRST_INTERVIEW_REJECTED: '一面淘汰',
  SECOND_INTERVIEW_PENDING: '二面',
  SECOND_INTERVIEW_PASSED: '二面通过',
  OFFER_PENDING: 'Offer待发',
  OFFER_SENT: 'Offer已发',
  HIRED: '已入职',
  REJECTED: '已淘汰',
};

export default function CandidateStageProgress({ stage }: { stage?: string | null }) {
  const terminalRejected = stage?.includes('REJECTED') || stage === 'REJECTED';
  const index = stage ? stageOrder.indexOf(stage) : -1;
  const percent = terminalRejected ? 100 : Math.max(8, index >= 0 ? ((index + 1) / stageOrder.length) * 100 : 18);
  const label = stageText[stage || ''] || stage || '跟进中';

  return (
    <Tooltip title={`当前阶段：${label}；流程：新投递 → 简历通过 → 一面 → 二面 → Offer → 入职`}>
      <Progress
        percent={Math.round(percent)}
        size="small"
        status={terminalRejected ? 'exception' : stage === 'HIRED' ? 'success' : 'active'}
        format={() => label}
      />
    </Tooltip>
  );
}
