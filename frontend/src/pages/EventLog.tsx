import { Button, Card, Descriptions, Drawer, Select, Space, Table, Tag } from 'antd';
import dayjs from 'dayjs';
import { useEffect, useMemo, useState } from 'react';
import { getEvents } from '../api/events';
import JsonViewer from '../components/JsonViewer';
import PageHeader from '../components/PageHeader';
import SourceTag from '../components/SourceTag';
import StatusTag from '../components/StatusTag';
import type { RecruitmentEvent } from '../types/event';

export default function EventLog() {
  const [data, setData] = useState<RecruitmentEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<RecruitmentEvent | null>(null);
  const [status, setStatus] = useState<string | undefined>();
  const [intent, setIntent] = useState<string | undefined>();

  const load = async () => {
    setLoading(true);
    try {
      setData(await getEvents());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const filtered = useMemo(
    () => data.filter((item) => (!status || item.status === status) && (!intent || item.intent === intent)),
    [data, status, intent],
  );

  const statusOptions = Array.from(new Set(data.map((item) => item.status))).map((value) => ({ label: value, value }));
  const intentOptions = Array.from(new Set(data.map((item) => item.intent))).map((value) => ({ label: value, value }));

  return (
    <>
      <PageHeader
        title="AI 处理与审计日志"
        description="记录每次 HR 消息输入、AI 抽取结果、置信度、工具调用和执行状态，便于企业落地后的追溯和问题排查。"
        extra={<Button onClick={load} loading={loading}>刷新</Button>}
      />
      <Card className="page-card">
        <div className="toolbar">
          <Space>
            <Select allowClear placeholder="筛选状态" style={{ width: 200 }} value={status} onChange={setStatus} options={statusOptions} />
            <Select allowClear placeholder="筛选意图" style={{ width: 240 }} value={intent} onChange={setIntent} options={intentOptions} />
          </Space>
        </div>
        <Table
          rowKey="id"
          loading={loading}
          dataSource={filtered}
          columns={[
            { title: 'ID', dataIndex: 'id', width: 80 },
            { title: '意图', dataIndex: 'intent', width: 190 },
            {
              title: '置信度',
              dataIndex: 'confidence',
              width: 130,
              render: (value: number) => {
                const percent = Math.round((value || 0) * 100);
                return percent < 60 ? <Tag color="orange">低置信度 {percent}%</Tag> : <Tag color="blue">{percent}%</Tag>;
              },
            },
            { title: '状态', dataIndex: 'status', width: 140, render: (value) => <StatusTag status={value} /> },
            { title: '发送人', dataIndex: 'sender', width: 120 },
            { title: '来源', dataIndex: 'source', width: 150, render: (value) => <SourceTag source={value} /> },
            { title: '原始消息', dataIndex: 'raw_text', ellipsis: true },
            {
              title: '时间',
              dataIndex: 'created_at',
              width: 180,
              render: (value) => dayjs(value).format('YYYY-MM-DD HH:mm'),
            },
            {
              title: '操作',
              fixed: 'right',
              width: 120,
              render: (_, record) => <Button type="link" onClick={() => setSelected(record)}>查看详情</Button>,
            },
          ]}
          scroll={{ x: 1380 }}
        />
      </Card>
      <Drawer title="审计详情" width={820} open={!!selected} onClose={() => setSelected(null)}>
        {selected ? (
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Descriptions size="small" bordered column={1}>
              <Descriptions.Item label="原始消息">{selected.raw_text}</Descriptions.Item>
              <Descriptions.Item label="执行摘要">{selected.action_summary || '-'}</Descriptions.Item>
              <Descriptions.Item label="错误原因">{selected.error_message || '-'}</Descriptions.Item>
            </Descriptions>
            <Card size="small" title="AI 抽取 JSON">
              <JsonViewer data={selected.extracted_json} />
            </Card>
          </Space>
        ) : null}
      </Drawer>
    </>
  );
}
