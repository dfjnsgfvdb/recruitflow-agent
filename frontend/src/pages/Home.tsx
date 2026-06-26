import {
  AuditOutlined,
  CloudSyncOutlined,
  DatabaseOutlined,
  DashboardOutlined,
  FileProtectOutlined,
  FileTextOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { Button, Card, Col, Row, Space, Steps, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';

const capabilities = [
  {
    icon: <RobotOutlined />,
    title: 'AI 自动记录',
    desc: '从自然语言招聘消息和简历 PDF 中抽取候选人、岗位、联系方式和流程状态，减少 HR 手工录入。',
  },
  {
    icon: <FileTextOutlined />,
    title: '简历智能解析',
    desc: '自动抽取学历、学校、专业、技能、项目经历和候选人画像，替代 HR 手工阅读与复制。',
  },
  {
    icon: <DashboardOutlined />,
    title: '实时同步看板',
    desc: '同步 MySQL 招聘台账、腾讯文档 Mock 和招聘看板，保证流程更新后数据即时可见。',
  },
  {
    icon: <AuditOutlined />,
    title: '企业级风控',
    desc: '状态机校验、高风险动作确认、AI 日志审计和 NEED_OCR 标记，保证自动化过程可控可追溯。',
  },
];

export default function Home() {
  const navigate = useNavigate();

  return (
    <div>
      <Card className="home-hero">
        <Row gutter={32} align="middle">
          <Col span={15}>
            <div className="hero-kicker">HR Recruiting Automation</div>
            <Typography.Title level={1}>RecruitFlow Agent 招聘流程自动化助手</Typography.Title>
            <Typography.Paragraph className="hero-subtitle">
              面向企业微信、企业微信群和腾讯在线文档场景，自动识别 HR 招聘沟通内容，结合候选人简历 PDF 完成建档、流程跟踪、文档同步和招聘看板更新。
            </Typography.Paragraph>
            <Space size={12}>
              <Button type="primary" size="large" onClick={() => navigate('/agent')}>
                开始演示
              </Button>
              <Button size="large" onClick={() => navigate('/resumes')}>
                查看简历中心
              </Button>
              <Button size="large" onClick={() => navigate('/dashboard')}>
                查看看板
              </Button>
            </Space>
          </Col>
          <Col span={9}>
            <div className="hero-panel">
              <DatabaseOutlined />
              <strong>自动招聘台账</strong>
              <span>企业微信消息、HR 备注和简历 PDF 进入系统后，自动沉淀为候选人、面试、事件日志、同步记录和待办动作。</span>
            </div>
          </Col>
        </Row>
      </Card>

      <Card title="业务闭环" className="page-card" style={{ marginTop: 18 }}>
        <Steps
          current={5}
          items={[
            { title: '企业微信消息' },
            { title: 'AI 信息抽取' },
            { title: '自动写入招聘台账' },
            { title: '同步腾讯文档/企业微信通知' },
            { title: '招聘看板更新' },
            { title: '高风险动作确认' },
          ]}
        />
      </Card>

      <Row gutter={[16, 16]} style={{ marginTop: 18 }}>
        {capabilities.map((item) => (
          <Col span={6} key={item.title}>
            <Card className="capability-card">
              <div className="capability-icon">{item.icon}</div>
              <h3>{item.title}</h3>
              <p>{item.desc}</p>
            </Card>
          </Col>
        ))}
      </Row>

      <Card className="page-card" style={{ marginTop: 18 }}>
        <Row align="middle" gutter={20}>
          <Col flex="none">
            <CloudSyncOutlined className="integration-large-icon" />
          </Col>
          <Col flex="auto">
            <Typography.Title level={4}>低成本落地路径</Typography.Title>
            <Typography.Paragraph style={{ marginBottom: 0 }}>
              MVP 阶段用 Web Demo 模拟企业微信消息，用 Mock 适配腾讯文档和企微通知，用可配置模型层支撑消息和简历解析。企业真实上线时，只需替换集成层，不影响 Agent、状态机和招聘台账数据结构。
            </Typography.Paragraph>
          </Col>
          <Col flex="none">
            <FileProtectOutlined className="integration-large-icon" />
          </Col>
        </Row>
      </Card>
    </div>
  );
}
