import { Tag } from 'antd';

const sourceMap: Record<string, { text: string; color: string }> = {
  WEB_DEMO: { text: 'Web Demo', color: 'blue' },
  WECOM_GROUP: { text: '企业微信群', color: 'green' },
  WECOM_PRIVATE: { text: '企业微信私聊', color: 'cyan' },
  TENCENT_DOC: { text: '腾讯文档备注', color: 'purple' },
  WECOM_MOCK: { text: '企微 Mock', color: 'green' },
};

export default function SourceTag({ source }: { source?: string | null }) {
  const item = source ? sourceMap[source] : undefined;
  return <Tag color={item?.color || 'default'}>{item?.text || source || '未知来源'}</Tag>;
}
