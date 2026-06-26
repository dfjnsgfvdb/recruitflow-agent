import { Progress, Space, Typography } from 'antd';

function getStrokeColor(score?: number | null) {
  if ((score || 0) >= 80) {
    return '#16a34a';
  }
  if ((score || 0) >= 60) {
    return '#d97706';
  }
  return '#dc2626';
}

function getLabel(score?: number | null) {
  if ((score || 0) >= 80) {
    return '较匹配';
  }
  if ((score || 0) >= 60) {
    return '一般匹配';
  }
  return '匹配较低';
}

export default function MatchScore({
  score,
  size = 'default',
}: {
  score?: number | null;
  size?: 'small' | 'default';
}) {
  if (score === undefined || score === null) {
    return <Typography.Text type="secondary">暂无匹配分</Typography.Text>;
  }

  const value = Math.max(0, Math.min(100, Number(score || 0)));

  return (
    <Space direction="vertical" size={4} style={{ width: '100%' }}>
      <Progress percent={value} strokeColor={getStrokeColor(value)} size={size} />
      <Typography.Text type="secondary">{getLabel(value)}</Typography.Text>
    </Space>
  );
}
