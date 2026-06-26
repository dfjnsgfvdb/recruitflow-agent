import { Button, Card, Empty, Modal, Popconfirm, Space, Table, message } from 'antd';
import dayjs from 'dayjs';
import { useEffect, useState } from 'react';
import { approvePendingAction, getPendingActions, rejectPendingAction } from '../api/confirmations';
import PageHeader from '../components/PageHeader';
import RiskTag from '../components/RiskTag';
import StatusTag from '../components/StatusTag';
import type { PendingAction } from '../types/confirmation';

export default function ConfirmationList() {
  const [data, setData] = useState<PendingAction[]>([]);
  const [loading, setLoading] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();
  const [modal, modalContextHolder] = Modal.useModal();

  const load = async () => {
    setLoading(true);
    try {
      setData(await getPendingActions());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const approve = (record: PendingAction) => {
    modal.confirm({
      title: '确认执行高风险动作？',
      content: `动作 ${record.action_type} 将真正写入候选人主数据，请确认已人工复核。`,
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

  return (
    <>
      {contextHolder}
      {modalContextHolder}
      <PageHeader
        title="待确认动作"
        description="高风险动作和异常状态跳转不会直接执行，需要 HR 负责人在这里确认或拒绝。"
        extra={<Button onClick={load} loading={loading}>刷新</Button>}
      />
      <Card className="page-card">
        {data.length === 0 && !loading ? (
          <Empty description="暂无待确认动作" />
        ) : (
          <Table
            rowKey="id"
            loading={loading}
            dataSource={data}
            columns={[
              { title: 'ID', dataIndex: 'id', width: 70 },
              { title: '动作类型', dataIndex: 'action_type', width: 180 },
              { title: '候选人ID', dataIndex: 'candidate_id', width: 110 },
              { title: '风险', dataIndex: 'risk_level', width: 110, render: (value) => <RiskTag risk={value} /> },
              { title: '原因', dataIndex: 'reason', ellipsis: true },
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
                width: 180,
                render: (_, record) => (
                  <Space>
                    <Button type="primary" danger={record.risk_level === 'HIGH'} onClick={() => approve(record)}>
                      确认执行
                    </Button>
                    <Popconfirm
                      title="拒绝该动作？"
                      description="拒绝后候选人主数据不会变更。"
                      okText="拒绝"
                      cancelText="取消"
                      onConfirm={() => reject(record)}
                    >
                      <Button>拒绝</Button>
                    </Popconfirm>
                  </Space>
                ),
              },
            ]}
            scroll={{ x: 1180 }}
          />
        )}
      </Card>
    </>
  );
}
