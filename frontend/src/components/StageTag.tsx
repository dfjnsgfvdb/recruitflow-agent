import { Tag } from 'antd';

const stageMap: Record<string, { text: string; color: string }> = {
  NEW: { text: '新投递', color: 'default' },
  SCREENING: { text: '简历筛选中', color: 'processing' },
  RESUME_PASSED: { text: '简历通过', color: 'blue' },
  RESUME_REJECTED: { text: '简历淘汰', color: 'red' },
  FIRST_INTERVIEW_PENDING: { text: '一面待面', color: 'cyan' },
  FIRST_INTERVIEW_PASSED: { text: '一面通过', color: 'green' },
  FIRST_INTERVIEW_REJECTED: { text: '一面淘汰', color: 'red' },
  SECOND_INTERVIEW_PENDING: { text: '二面待面', color: 'geekblue' },
  SECOND_INTERVIEW_PASSED: { text: '二面通过', color: 'green' },
  OFFER_PENDING: { text: 'Offer待发', color: 'orange' },
  OFFER_SENT: { text: 'Offer已发', color: 'gold' },
  HIRED: { text: '已入职', color: 'green' },
  REJECTED: { text: '已淘汰', color: 'red' },
};

export default function StageTag({ stage }: { stage?: string | null }) {
  const item = stage ? stageMap[stage] : undefined;
  return <Tag color={item?.color || 'default'}>{item?.text || stage || '未设置'}</Tag>;
}
