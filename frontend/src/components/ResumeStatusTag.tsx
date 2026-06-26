import { Tag } from 'antd';

const statusMap: Record<string, { text: string; color: string }> = {
  PENDING: { text: '解析中', color: 'processing' },
  SUCCESS: { text: '解析成功', color: 'green' },
  FAILED: { text: '解析失败', color: 'red' },
  NEED_OCR: { text: '需要 OCR', color: 'gold' },
  NEED_REVIEW: { text: '需要人工复核', color: 'orange' },
};

export default function ResumeStatusTag({ status }: { status?: string | null }) {
  const item = status ? statusMap[status] : undefined;
  return <Tag color={item?.color || 'default'}>{item?.text || status || '未知状态'}</Tag>;
}
