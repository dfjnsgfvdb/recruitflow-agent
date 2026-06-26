import { Tag } from 'antd';

const riskMap: Record<string, { text: string; color: string }> = {
  LOW: { text: '低风险', color: 'green' },
  MEDIUM: { text: '中风险', color: 'orange' },
  HIGH: { text: '高风险', color: 'red' },
};

export default function RiskTag({ risk }: { risk?: string | null }) {
  const item = risk ? riskMap[risk] : undefined;
  return <Tag color={item?.color || 'default'}>{item?.text || risk || '未知'}</Tag>;
}
