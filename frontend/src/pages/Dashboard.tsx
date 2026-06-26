import { Alert, Button, Card, Col, Empty, Row, Statistic, Table } from 'antd';
import type { EChartsOption } from 'echarts';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import { useEffect, useMemo, useState } from 'react';
import { getPendingActions } from '../api/confirmations';
import { getDashboardSummary } from '../api/dashboard';
import PageHeader from '../components/PageHeader';
import StatusTag from '../components/StatusTag';
import type { DashboardSummary } from '../types/dashboard';

export default function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [summary, pending] = await Promise.all([getDashboardSummary(), getPendingActions()]);
      setData(summary);
      setPendingCount(pending.length);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const stageOption = useMemo<EChartsOption>(
    () => ({
      tooltip: { trigger: 'axis' },
      grid: { left: 110, right: 24, top: 36, bottom: 28 },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: data?.stage_distribution.map((item) => item.stage) || [] },
      series: [
        {
          type: 'bar',
          data: data?.stage_distribution.map((item) => item.count) || [],
          itemStyle: { color: '#2155d9', borderRadius: [0, 6, 6, 0] },
        },
      ],
    }),
    [data],
  );

  const positionOption = useMemo<EChartsOption>(
    () => ({
      tooltip: { trigger: 'axis' },
      grid: { left: 48, right: 24, top: 36, bottom: 70 },
      xAxis: {
        type: 'category',
        data: data?.position_distribution.map((item) => item.position_name) || [],
        axisLabel: { rotate: 25 },
      },
      yAxis: { type: 'value' },
      series: [
        {
          type: 'bar',
          data: data?.position_distribution.map((item) => item.count) || [],
          itemStyle: { color: '#16a34a', borderRadius: [6, 6, 0, 0] },
        },
      ],
    }),
    [data],
  );

  return (
    <>
      <PageHeader
        title="招聘数据看板"
        description="自动汇总企业微信招聘消息沉淀出的候选人、面试、待确认动作和超时跟进情况。"
        extra={<Button onClick={load} loading={loading}>刷新</Button>}
      />
      <Row gutter={[16, 16]}>
        {[
          ['候选人总数', data?.total_candidates || 0],
          ['今日自动记录', data?.today_new_candidates || 0],
          ['待面试人数', data?.pending_interviews || 0],
          ['超时未跟进', data?.timeout_followup_count || 0],
          ['待确认高风险动作', pendingCount],
        ].map(([title, value]) => (
          <Col span={24 / 5} key={title}>
            <Card className="stat-card" loading={loading}>
              <Statistic title={title} value={value as number} />
            </Card>
          </Col>
        ))}
      </Row>

      <Card className="page-card" style={{ marginTop: 16 }}>
        <Alert
          type="info"
          showIcon
          message="招聘效率说明"
          description="系统自动从招聘沟通中提取候选人信息，并同步更新看板，减少 HR 在企业微信和腾讯文档之间重复复制粘贴。"
        />
      </Card>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="招聘阶段分布" className="page-card">
            {data?.stage_distribution?.length ? <ReactECharts option={stageOption} style={{ height: 320 }} /> : <Empty />}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="岗位候选人数分布" className="page-card">
            {data?.position_distribution?.length ? <ReactECharts option={positionOption} style={{ height: 320 }} /> : <Empty />}
          </Card>
        </Col>
      </Row>
      <Card title="最近自动化事件" className="page-card" style={{ marginTop: 16 }}>
        <Table
          rowKey="id"
          loading={loading}
          dataSource={data?.recent_events || []}
          pagination={false}
          columns={[
            { title: 'ID', dataIndex: 'id', width: 80 },
            { title: '意图', dataIndex: 'intent', width: 180 },
            { title: '状态', dataIndex: 'status', width: 140, render: (value) => <StatusTag status={value} /> },
            { title: '发送人', dataIndex: 'sender', width: 120 },
            { title: '时间', dataIndex: 'created_at', width: 180, render: (value) => dayjs(value).format('YYYY-MM-DD HH:mm') },
          ]}
        />
      </Card>
    </>
  );
}
