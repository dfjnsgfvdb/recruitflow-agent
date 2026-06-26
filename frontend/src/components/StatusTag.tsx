import { Tag } from 'antd';

const statusMap: Record<string, { text: string; color: string }> = {
  SUCCESS: { text: '成功', color: 'green' },
  FAILED: { text: '失败', color: 'red' },
  NEED_CLARIFICATION: { text: '需要追问', color: 'orange' },
  NEED_CONFIRMATION: { text: '待确认', color: 'gold' },
  PENDING: { text: '待处理', color: 'processing' },
  EXECUTED: { text: '已执行', color: 'green' },
  REJECTED: { text: '已拒绝', color: 'red' },
};

export default function StatusTag({ status }: { status?: string | null }) {
  const item = status ? statusMap[status] : undefined;
  return <Tag color={item?.color || 'default'}>{item?.text || status || '未知'}</Tag>;
}
