import { Alert, Button, Card, Descriptions, Drawer, Empty, Input, List, Select, Space, Table, Tabs, Typography } from 'antd';
import dayjs from 'dayjs';
import { useEffect, useMemo, useState } from 'react';
import { getCandidates } from '../api/candidates';
import { getEvents } from '../api/events';
import { getCandidateResume } from '../api/resumes';
import CandidateStageProgress from '../components/CandidateStageProgress';
import JsonViewer from '../components/JsonViewer';
import MaskedText from '../components/MaskedText';
import MatchScore from '../components/MatchScore';
import PageHeader from '../components/PageHeader';
import ResumeInsightCard from '../components/ResumeInsightCard';
import ResumeStatusTag from '../components/ResumeStatusTag';
import SkillTags from '../components/SkillTags';
import StageTag from '../components/StageTag';
import StatusTag from '../components/StatusTag';
import type { Candidate } from '../types/candidate';
import type { RecruitmentEvent } from '../types/event';
import type { CandidateResumeResponse, ResumeParseResult } from '../types/resume';

export default function CandidateList() {
  const [data, setData] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [keyword, setKeyword] = useState('');
  const [stage, setStage] = useState<string | undefined>();
  const [selected, setSelected] = useState<Candidate | null>(null);
  const [candidateResume, setCandidateResume] = useState<CandidateResumeResponse | null>(null);
  const [candidateEvents, setCandidateEvents] = useState<RecruitmentEvent[]>([]);
  const [drawerLoading, setDrawerLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      setData(await getCandidates());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (!selected) {
      setCandidateResume(null);
      setCandidateEvents([]);
      return;
    }

    const loadDrawerData = async () => {
      setDrawerLoading(true);
      try {
        const [events] = await Promise.all([
          getEvents(),
          (async () => {
            try {
              const resume = await getCandidateResume(selected.id, { silent: true });
              setCandidateResume(resume);
            } catch {
              setCandidateResume(null);
            }
          })(),
        ]);
        setCandidateEvents(events.filter((item) => item.candidate_id === selected.id));
      } finally {
        setDrawerLoading(false);
      }
    };

    void loadDrawerData();
  }, [selected]);

  const filtered = useMemo(() => {
    const text = keyword.trim().toLowerCase();
    return data.filter((item) => {
      const matchText =
        !text ||
        item.name.toLowerCase().includes(text) ||
        (item.position_name || '').toLowerCase().includes(text) ||
        (item.phone || '').includes(text);
      const matchStage = !stage || item.stage === stage;
      return matchText && matchStage;
    });
  }, [data, keyword, stage]);

  const stageOptions = Array.from(new Set(data.map((item) => item.stage))).map((value) => ({ label: value, value }));
  const parsedResume = candidateResume?.resume_file?.parsed_json as ResumeParseResult | undefined;
  const parsedCandidate = (parsedResume?.candidate || {}) as Record<string, unknown>;

  return (
    <>
      <PageHeader
        title="候选人招聘台账"
        description="AI Agent 自动记录和更新的候选人结构化数据，可替代人工维护腾讯文档招聘表。"
        extra={
          <Button onClick={load} loading={loading}>
            刷新
          </Button>
        }
      />
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="候选人来源于企业微信消息识别、批量导入或腾讯文档备注同步。"
        description="系统会自动维护招聘阶段、跟进时间和候选人画像，减少 HR 在企业微信和腾讯文档之间重复复制粘贴。"
      />
      <Card className="page-card">
        <div className="toolbar">
          <Space>
            <Input.Search
              allowClear
              placeholder="搜索姓名 / 岗位 / 手机号"
              style={{ width: 300 }}
              onSearch={setKeyword}
              onChange={(event) => setKeyword(event.target.value)}
            />
            <Select
              allowClear
              placeholder="筛选阶段"
              style={{ width: 220 }}
              value={stage}
              onChange={setStage}
              options={stageOptions}
            />
          </Space>
        </div>
        <Table
          rowKey="id"
          loading={loading}
          dataSource={filtered}
          columns={[
            { title: 'ID', dataIndex: 'id', width: 70 },
            { title: '姓名', dataIndex: 'name', width: 120 },
            { title: '手机号', dataIndex: 'phone', width: 150, render: (value) => <MaskedText value={value} /> },
            { title: '岗位', dataIndex: 'position_name', width: 220 },
            { title: '来源', dataIndex: 'source', width: 120 },
            { title: '阶段', dataIndex: 'stage', width: 150, render: (value) => <StageTag stage={value} /> },
            { title: '流程进度', dataIndex: 'stage', width: 260, render: (value) => <CandidateStageProgress stage={value} /> },
            {
              title: '最近跟进',
              dataIndex: 'last_followup_at',
              width: 180,
              render: (value) => (value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '-'),
            },
            {
              title: '更新时间',
              dataIndex: 'updated_at',
              width: 180,
              render: (value) => dayjs(value).format('YYYY-MM-DD HH:mm'),
            },
            {
              title: '操作',
              fixed: 'right',
              width: 120,
              render: (_, record) => (
                <Button type="link" onClick={() => setSelected(record)}>
                  查看详情
                </Button>
              ),
            },
          ]}
          scroll={{ x: 1420 }}
        />
      </Card>
      <Drawer
        title={selected ? `${selected.name} · 候选人详情` : '候选人详情'}
        width={860}
        open={!!selected}
        onClose={() => setSelected(null)}
        destroyOnClose
      >
        {!selected ? null : (
          <Tabs
            items={[
              {
                key: 'base',
                label: '基础信息',
                children: (
                  <Descriptions column={2} bordered size="small">
                    <Descriptions.Item label="姓名">{selected.name}</Descriptions.Item>
                    <Descriptions.Item label="岗位">{selected.position_name || '-'}</Descriptions.Item>
                    <Descriptions.Item label="手机号">
                      <MaskedText value={selected.phone} />
                    </Descriptions.Item>
                    <Descriptions.Item label="邮箱">{selected.email || '-'}</Descriptions.Item>
                    <Descriptions.Item label="学历">{selected.education || '-'}</Descriptions.Item>
                    <Descriptions.Item label="学校">{selected.school || '-'}</Descriptions.Item>
                    <Descriptions.Item label="专业">{selected.major || '-'}</Descriptions.Item>
                    <Descriptions.Item label="毕业年份">{selected.graduation_year || '-'}</Descriptions.Item>
                    <Descriptions.Item label="工作年限">{selected.work_years || '-'}</Descriptions.Item>
                    <Descriptions.Item label="简历解析状态">
                      <ResumeStatusTag status={selected.resume_parse_status} />
                    </Descriptions.Item>
                    <Descriptions.Item label="技能标签" span={2}>
                      <SkillTags skills={selected.skills} />
                    </Descriptions.Item>
                    <Descriptions.Item label="简历摘要" span={2}>
                      {selected.resume_summary || selected.experience_summary || '-'}
                    </Descriptions.Item>
                  </Descriptions>
                ),
              },
              {
                key: 'flow',
                label: '招聘流程',
                children: (
                  <Space direction="vertical" size={16} style={{ width: '100%' }}>
                    <Card size="small">
                      <CandidateStageProgress stage={selected.stage} />
                    </Card>
                    <Descriptions column={2} bordered size="small">
                      <Descriptions.Item label="当前阶段">
                        <StageTag stage={selected.stage} />
                      </Descriptions.Item>
                      <Descriptions.Item label="来源">{selected.source || '-'}</Descriptions.Item>
                      <Descriptions.Item label="最近跟进时间">
                        {selected.last_followup_at ? dayjs(selected.last_followup_at).format('YYYY-MM-DD HH:mm') : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="最后更新时间">{dayjs(selected.updated_at).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
                    </Descriptions>
                  </Space>
                ),
              },
              {
                key: 'resume',
                label: '简历画像',
                children: drawerLoading ? (
                  <Card loading />
                ) : !candidateResume ? (
                  <Empty description="暂无简历 PDF，建议上传简历以生成候选人画像和岗位匹配报告。" />
                ) : (
                  <Space direction="vertical" size={16} style={{ width: '100%' }}>
                    <Descriptions column={2} bordered size="small">
                      <Descriptions.Item label="简历解析状态">
                        <ResumeStatusTag status={candidateResume.resume_file.parse_status} />
                      </Descriptions.Item>
                      <Descriptions.Item label="岗位匹配分">
                        <MatchScore score={candidateResume.screening_report?.match_score || selected.match_score} size="small" />
                      </Descriptions.Item>
                      <Descriptions.Item label="学历 / 学校 / 专业" span={2}>
                        {[parsedCandidate.education, parsedCandidate.school, parsedCandidate.major].filter(Boolean).join(' / ') || '-'}
                      </Descriptions.Item>
                    </Descriptions>
                    <ResumeInsightCard
                      summary={candidateResume.resume_file.resume_summary}
                      skills={candidateResume.resume_file.skill_tags}
                      parseResult={parsedResume}
                      screeningReport={candidateResume.screening_report}
                    />
                    <Card title="项目经历" size="small">
                      <JsonViewer data={parsedResume?.project_experiences} />
                    </Card>
                    <Card title="工作经历" size="small">
                      <JsonViewer data={parsedResume?.work_experiences} />
                    </Card>
                  </Space>
                ),
              },
              {
                key: 'logs',
                label: 'AI 日志',
                children: candidateEvents.length === 0 ? (
                  <Empty description="暂无与该候选人关联的 AI 处理日志。" />
                ) : (
                  <List
                    itemLayout="vertical"
                    dataSource={candidateEvents}
                    renderItem={(item) => (
                      <List.Item
                        extra={<StatusTag status={item.status} />}
                        actions={[<span key="time">{dayjs(item.created_at).format('YYYY-MM-DD HH:mm')}</span>]}
                      >
                        <List.Item.Meta title={item.intent} description={item.raw_text} />
                        <Typography.Paragraph type="secondary" style={{ marginBottom: 8 }}>
                          置信度：{Math.round(item.confidence * 100)}%
                        </Typography.Paragraph>
                        <JsonViewer data={item.extracted_json} />
                      </List.Item>
                    )}
                  />
                ),
              },
            ]}
          />
        )}
      </Drawer>
    </>
  );
}
