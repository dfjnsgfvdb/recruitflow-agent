import {
  ApiOutlined,
  CloudSyncOutlined,
  DatabaseOutlined,
  MessageOutlined,
  RobotOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { Card, Col, Row, Tag, Typography } from 'antd';
import PageHeader from '../components/PageHeader';

const integrations = [
  {
    icon: <MessageOutlined />,
    title: '企业微信消息接入',
    status: 'Mock',
    color: 'blue',
    desc: '当前通过 Web Demo 模拟企业微信消息，企业落地时可替换为企业微信回调适配器。',
  },
  {
    icon: <TeamOutlined />,
    title: '企业微信群通知',
    status: 'Mock',
    color: 'green',
    desc: '当前记录通知日志，企业落地时可替换为群机器人 Webhook。',
  },
  {
    icon: <CloudSyncOutlined />,
    title: '腾讯文档同步',
    status: 'Mock',
    color: 'purple',
    desc: '当前写入同步日志，企业落地时可替换为腾讯文档 API。',
  },
  {
    icon: <RobotOutlined />,
    title: '大模型服务',
    status: 'Configurable',
    color: 'orange',
    desc: '支持 Mock / OpenAI-compatible / Qwen / DeepSeek。',
  },
  {
    icon: <DatabaseOutlined />,
    title: 'MySQL 招聘台账',
    status: 'Connected',
    color: 'green',
    desc: '存储候选人、面试、事件日志和待确认动作。',
  },
];

export default function Integrations() {
  return (
    <>
      <PageHeader
        title="同步与集成"
        description="展示企业微信、腾讯文档、大模型服务和 MySQL 招聘台账的适配状态，说明从 Demo 到企业落地的替换路径。"
      />
      <Row gutter={[16, 16]}>
        {integrations.map((item) => (
          <Col span={8} key={item.title}>
            <Card className="integration-card">
              <div className="integration-icon">{item.icon}</div>
              <div className="integration-title-row">
                <h3>{item.title}</h3>
                <Tag color={item.color}>{item.status}</Tag>
              </div>
              <p>{item.desc}</p>
            </Card>
          </Col>
        ))}
      </Row>

      <Card className="page-card" style={{ marginTop: 18 }}>
        <Typography.Title level={4}>
          <ApiOutlined /> 低成本落地说明
        </Typography.Title>
        <Typography.Paragraph>
          MVP 阶段保留适配层，不强依赖企业认证权限；企业真实上线时只需替换 integrations 层，不影响 Agent 和业务数据层。后端当前已将腾讯文档同步和企业微信通知封装为 Mock 工具，后续可以平滑替换为真实 API。
        </Typography.Paragraph>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          当前后端暂未暴露 sync_logs 查询接口，因此本页先展示 Mock 状态和集成说明。后续新增接口后，可直接在这里补充同步日志表。
        </Typography.Paragraph>
      </Card>
    </>
  );
}
