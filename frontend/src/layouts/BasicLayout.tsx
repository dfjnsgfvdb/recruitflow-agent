import {
  AuditOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
  CloudSyncOutlined,
  FileSearchOutlined,
  FileTextOutlined,
  HomeOutlined,
  RobotOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { Layout, Menu, Typography } from 'antd';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/home', icon: <HomeOutlined />, label: '首页总览' },
  { key: '/agent', icon: <RobotOutlined />, label: '企业微信消息处理' },
  { key: '/resumes', icon: <FileTextOutlined />, label: '简历解析中心' },
  { key: '/dashboard', icon: <BarChartOutlined />, label: '招聘数据看板' },
  { key: '/candidates', icon: <TeamOutlined />, label: '候选人台账' },
  { key: '/tasks', icon: <CheckCircleOutlined />, label: '待办中心' },
  { key: '/integrations', icon: <CloudSyncOutlined />, label: '同步与集成' },
  { key: '/events', icon: <FileSearchOutlined />, label: 'AI 处理日志' },
];

export default function BasicLayout() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <Layout className="app-shell">
      <Sider width={236} className="app-sider">
        <div className="brand">
          <AuditOutlined />
          <div>
            <strong>RecruitFlow</strong>
            <span>Agent Console</span>
          </div>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          className="side-menu"
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <Typography.Title level={4} style={{ margin: 0 }}>
            RecruitFlow Agent 招聘自动化工作台
          </Typography.Title>
          <span className="header-subtitle">企业微信招聘消息自动记录 · 腾讯文档同步 · 招聘流程自动跟踪</span>
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
