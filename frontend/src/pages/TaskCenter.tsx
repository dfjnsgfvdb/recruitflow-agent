import { Alert, Button, Card, Empty, Modal, Popconfirm, Space, Table, Tabs, Tag, message } from 'antd';
import dayjs from 'dayjs';
import { useEffect, useMemo, useState } from 'react';
import { approvePendingAction, getPendingActions, rejectPendingAction } from '../api/confirmations';
import { getCandidates } from '../api/candidates';
import CandidateStageProgress from '../components/CandidateStageProgress';
import MaskedText from '../components/MaskedText';
import PageHeader from '../components/PageHeader';
import RiskTag from '../components/RiskTag';
import StageTag from '../components/StageTag';
import StatusTag from '../components/StatusTag';
import type { Candidate } from '../types/candidate';
import type { PendingAction } from '../types/confirmation';

const actionText: Record<string, string> = {
  reject_candidate: '淘汰候选人',
  send_offer: '发送 Offer',
  mark_hired: '标记入职',
  update_candidate_stage: '更新招聘阶段',
  create_interview: '创建面试安排',
};

export default function TaskCenter() {
  const [pendingActions, setPendingActions] = useState<PendingAction[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();
  const [modal, modalContextHolder] = Modal.useModal();

  const load = async () => {
    setLoading(true);
    try {
      const [pending, candidateList] = await Promise.all([getPendingActions(), getCandidates()]);
      setPendingActions(pending);
      setCandidates(candidateList);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const timeoutCandidates = useMemo(() => {
    const now = dayjs();
    return candidates
      .filter((item) => item.last_followup_at && now.diff(dayjs(item.last_followup_at), 'hour') > 48)
      .map((item) => ({ ...item, timeoutHours: now.diff(dayjs(item.last_followup_at), 'hour') }));
  }, [candidates]);

  const approve = (record: PendingAction) => {
    modal.confirm({
      title: `确认执行：${actionText[record.action_type] || record.action_type}`,
      content: '该动作会真正修改候选人招聘状态，确认后将写入招聘台账和操作日志，是否继续？',
      okText: '确认执行',
      cancelText: '取消',
      okButtonProps: { danger: record.risk_level === 'HIGH' },
      async onOk() {
        const response = await approvePendingAction(record.id);
        if (response.success) {
          messageApi.success(response.message);
          await load();
        } else {
          messageApi.error(response.message);
        }
      },
    });
  };

  const reject = async (record: PendingAction) => {
    const response = await rejectPendingAction(record.id, 'HR负责人', '前端人工拒绝：暂不执行该高风险动作');
    if (response.success) {
      messageApi.success(response.message);
      await load();
    } else {
      messageApi.error(response.message);
    }
  };

  const copyReminder = async (record: Candidate & { timeoutHours: number }) => {
    const text = `请及时跟进候选人${record.name}，当前阶段${record.stage}，已超过48小时未更新。`;
    await navigator.clipboard.writeText(text);
    messageApi.success('提醒文案已复制');
  };

  return (
    <>
      {contextHolder}
      {modalContextHolder}
      <PageHeader
        title="待办中心"
        description="集中处理高风险确认和超时未跟进提醒，解决企业微信沟通分散、腾讯文档维护滞后的问题。"
        extra={<Button onClick={load} loading={loading}>刷新</Button>}
      />
      <Tabs
        items={[
          {
            key: 'risk',
            label: `高风险确认 (${pendingActions.length})`,
            children: (
              <Card className="page-card">
                <Alert
                  type="warning"
                  showIcon
                  style={{ marginBottom: 16 }}
                  message="高风险动作不会自动执行"
                  description="淘汰候选人、发送 Offer、标记入职或异常状态跳转必须由 HR 负责人确认后才会写入招聘台账。"
                />
                {pendingActions.length === 0 && !loading ? (
                  <Empty description="暂无待确认动作，说明当前没有高风险操作待处理" />
                ) : (
                  <Table
                    rowKey="id"
                    loading={loading}
                    dataSource={pendingActions}
                    columns={[
                      { title: 'ID', dataIndex: 'id', width: 70 },
                      {
                        title: '业务动作',
                        dataIndex: 'action_type',
                        width: 180,
                        render: (value) => <Tag color="volcano">{actionText[value] || value}</Tag>,
                      },
                      { title: '候选人ID', dataIndex: 'candidate_id', width: 110 },
                      { title: '风险', dataIndex: 'risk_level', width: 110, render: (value) => <RiskTag risk={value} /> },
                      { title: '风险原因', dataIndex: 'reason', ellipsis: true },
                      { title: '请求人', dataIndex: 'requested_by', width: 120 },
                      { title: '状态', dataIndex: 'status', width: 120, render: (value) => <StatusTag status={value} /> },
                      {
                        title: '创建时间',
                        dataIndex: 'created_at',
                        width: 180,
                        render: (value) => dayjs(value).format('YYYY-MM-DD HH:mm'),
                      },
                      {
                        title: '操作',
                        fixed: 'right',
                        width: 190,
                        render: (_, record) => (
                          <Space>
                            <Button type="primary" danger={record.risk_level === 'HIGH'} onClick={() => approve(record)}>
                              确认执行
                            </Button>
                            <Popconfirm title="拒绝该动作？" okText="拒绝" cancelText="取消" onConfirm={() => reject(record)}>
                              <Button>拒绝</Button>
                            </Popconfirm>
                          </Space>
                        ),
                      },
                    ]}
                    scroll={{ x: 1220 }}
                  />
                )}
              </Card>
            ),
          },
          {
            key: 'timeout',
            label: `超时未跟进 (${timeoutCandidates.length})`,
            children: (
              <Card className="page-card">
                <Alert
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                  message="从候选人 last_followup_at 前端计算超过 48 小时未更新的数据"
                  description="用于体现系统对招聘流程时效性的自动提醒能力，避免 HR 在企业微信和腾讯文档之间遗漏跟进。"
                />
                {timeoutCandidates.length === 0 && !loading ? (
                  <Empty description="暂无超时未跟进候选人" />
                ) : (
                  <Table
                    rowKey="id"
                    loading={loading}
                    dataSource={timeoutCandidates}
                    columns={[
                      { title: '候选人', dataIndex: 'name', width: 120 },
                      { title: '手机号', dataIndex: 'phone', width: 150, render: (value) => <MaskedText value={value} /> },
                      { title: '岗位', dataIndex: 'position_name', width: 220 },
                      { title: '当前阶段', dataIndex: 'stage', width: 160, render: (value) => <StageTag stage={value} /> },
                      { title: '流程进度', dataIndex: 'stage', width: 240, render: (value) => <CandidateStageProgress stage={value} /> },
                      {
                        title: '最近跟进时间',
                        dataIndex: 'last_followup_at',
                        width: 180,
                        render: (value) => dayjs(value).format('YYYY-MM-DD HH:mm'),
                      },
                      { title: '超时小时数', dataIndex: 'timeoutHours', width: 120 },
                      {
                        title: '操作',
                        width: 150,
                        render: (_, record) => <Button onClick={() => copyReminder(record)}>复制提醒文案</Button>,
                      },
                    ]}
                    scroll={{ x: 1280 }}
                  />
                )}
              </Card>
            ),
          },
        ]}
      />
    </>
  );
}
