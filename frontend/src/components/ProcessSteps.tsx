import {
  CheckCircleOutlined,
  CloudSyncOutlined,
  FileDoneOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons';
import { Steps } from 'antd';

interface ProcessStepsProps {
  current?: number;
}

export default function ProcessSteps({ current = 5 }: ProcessStepsProps) {
  return (
    <Steps
      size="small"
      current={current}
      items={[
        { title: '接收消息', icon: <FileDoneOutlined /> },
        { title: 'AI 抽取', icon: <RobotOutlined /> },
        { title: '状态校验', icon: <SafetyCertificateOutlined /> },
        { title: '工具执行', icon: <CheckCircleOutlined /> },
        { title: '同步更新', icon: <CloudSyncOutlined /> },
      ]}
    />
  );
}
