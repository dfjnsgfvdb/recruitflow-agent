import {
  Alert,
  Button,
  Card,
  Descriptions,
  Drawer,
  Form,
  Input,
  Modal,
  Space,
  Table,
  Typography,
  Upload,
  message as antdMessage,
} from 'antd';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';
import dayjs from 'dayjs';
import { useEffect, useMemo, useState } from 'react';
import { getCandidateResume, getResumes, reparseResume, screenResume, uploadResume } from '../api/resumes';
import JsonViewer from '../components/JsonViewer';
import MatchScore from '../components/MatchScore';
import PageHeader from '../components/PageHeader';
import ResumeInsightCard from '../components/ResumeInsightCard';
import ResumeStatusTag from '../components/ResumeStatusTag';
import SkillTags from '../components/SkillTags';
import type {
  CandidateResumeResponse,
  ResumeFile,
  ResumeParseResult,
  ResumeScreeningReport,
} from '../types/resume';

const { Dragger } = Upload;
const { TextArea } = Input;

type ResumeFormValues = {
  message?: string;
  position_name?: string;
  job_requirements?: string;
  sender?: string;
  source?: string;
};

export default function ResumeCenter() {
  const [form] = Form.useForm<ResumeFormValues>();
  const [screenForm] = Form.useForm<{ position_name: string; job_requirements?: string }>();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [reparseLoadingId, setReparseLoadingId] = useState<number | null>(null);
  const [screeningRow, setScreeningRow] = useState<ResumeFile | null>(null);
  const [resumes, setResumes] = useState<ResumeFile[]>([]);
  const [resumeDetails, setResumeDetails] = useState<Record<number, CandidateResumeResponse | null>>({});
  const [selected, setSelected] = useState<ResumeFile | null>(null);
  const [messageApi, contextHolder] = antdMessage.useMessage();

  const load = async () => {
    setLoading(true);
    try {
      const list = await getResumes();
      setResumes(list);
      const detailPairs = await Promise.all(
        list
          .filter((item) => item.candidate_id)
          .map(async (item) => {
            try {
              const detail = await getCandidateResume(item.candidate_id as number, { silent: true });
              return [item.id, detail.resume_file.id === item.id ? detail : null] as const;
            } catch {
              return [item.id, null] as const;
            }
          }),
      );
      setResumeDetails(Object.fromEntries(detailPairs));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const uploadProps: UploadProps = {
    accept: '.pdf,application/pdf',
    multiple: false,
    beforeUpload: () => false,
    fileList,
    onChange: ({ fileList: nextFileList }) => setFileList(nextFileList.slice(-1)),
    onRemove: () => {
      setFileList([]);
      return true;
    },
  };

  const handleUpload = async () => {
    const values = await form.validateFields();
    if (!fileList[0]?.originFileObj) {
      messageApi.warning('请先选择一份 PDF 简历。');
      return;
    }

    const formData = new FormData();
    formData.append('file', fileList[0].originFileObj as File);
    formData.append('sender', values.sender || 'HR小王');
    formData.append('source', values.source || 'WEB_DEMO');
    if (values.message) {
      formData.append('message', values.message);
    }
    if (values.position_name) {
      formData.append('position_name', values.position_name);
    }
    if (values.job_requirements) {
      formData.append('job_requirements', values.job_requirements);
    }

    setSubmitLoading(true);
    try {
        const response = await uploadResume(formData);
        if (response.success) {
          messageApi.success('简历上传成功，已完成解析和建档。');
          setFileList([]);
          form.resetFields();
          form.setFieldsValue({ sender: 'HR小王', source: 'WEB_DEMO' });
          await load();
          if (response.resume_file) {
            setSelected(response.resume_file as ResumeFile);
          }
        } else {
        messageApi.error(response.message || '简历上传失败');
      }
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleReparse = async (resume: ResumeFile) => {
    setReparseLoadingId(resume.id);
    try {
      await reparseResume(resume.id);
      messageApi.success('简历已重新解析。');
      await load();
    } finally {
      setReparseLoadingId(null);
    }
  };

  const detailForSelected = selected ? resumeDetails[selected.id] : null;
  const screeningReport = selected ? detailForSelected?.screening_report || null : null;
  const parsedJson = useMemo(() => (selected?.parsed_json || {}) as ResumeParseResult & Record<string, unknown>, [selected]);
  const parsedCandidate = (parsedJson.candidate || {}) as Record<string, unknown>;
  const candidateText = (key: string) => {
    const value = parsedCandidate[key];
    return typeof value === 'string' && value ? value : '-';
  };

  return (
    <>
      {contextHolder}
      <PageHeader
        title="简历解析中心"
        description="上传候选人简历 PDF，系统自动抽取学历、技能、项目经历，并生成岗位匹配报告和建议面试问题。"
      />
      <Alert
        type="warning"
        showIcon
        style={{ marginBottom: 16 }}
        message="当前存在部分候选人缺少简历或简历解析失败，建议进入数据质量中心统一处理。"
        description="简历 PDF 是招聘建档的重要数据来源。系统会明确标记 NEED_OCR 和 NEED_REVIEW，不会让扫描件或冲突字段默默失败。"
      />
      <Card title="上传并解析简历" className="page-card" style={{ marginBottom: 16 }}>
        <Form
          form={form}
          layout="vertical"
          initialValues={{ sender: 'HR小王', source: 'WEB_DEMO', position_name: 'AI Agent开发实习生' }}
        >
          <Form.Item label="候选人简历 PDF">
            <Dragger {...uploadProps}>
              <Typography.Title level={5} style={{ marginBottom: 8 }}>
                上传候选人简历 PDF
              </Typography.Title>
              <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
                系统会自动抽取候选人画像和岗位匹配报告，替代 HR 手工阅读简历和维护腾讯文档。
              </Typography.Paragraph>
            </Dragger>
          </Form.Item>
          <Form.Item name="message" label="HR 备注">
            <TextArea rows={4} placeholder="例如：候选人张三，投递AI Agent开发实习生，简历通过，来源Boss直聘。" />
          </Form.Item>
          <Form.Item name="position_name" label="应聘岗位">
            <Input placeholder="例如：AI Agent开发实习生" />
          </Form.Item>
          <Form.Item name="job_requirements" label="岗位要求">
            <TextArea rows={4} placeholder="可选。用于生成更准确的岗位匹配分、缺失项和建议面试问题。" />
          </Form.Item>
          <Space>
            <Button type="primary" loading={submitLoading} onClick={handleUpload}>
              上传并解析
            </Button>
            <Button
              onClick={() => {
                setFileList([]);
                form.resetFields();
                form.setFieldsValue({ sender: 'HR小王', source: 'WEB_DEMO' });
              }}
            >
              清空
            </Button>
          </Space>
        </Form>
      </Card>
      <Card className="page-card">
        <div className="toolbar">
          <Typography.Text type="secondary">
            AI 会结合简历 PDF、HR 备注和岗位要求，自动生成候选人画像与面试建议。
          </Typography.Text>
          <Button onClick={load} loading={loading}>
            刷新
          </Button>
        </div>
        <Table
          rowKey="id"
          loading={loading}
          dataSource={resumes}
          columns={[
            { title: '文件名', dataIndex: 'original_filename', width: 220 },
            { title: '候选人 ID', dataIndex: 'candidate_id', width: 100, render: (value) => value || '-' },
            { title: '解析状态', dataIndex: 'parse_status', width: 140, render: (value) => <ResumeStatusTag status={value} /> },
            {
              title: '置信度',
              dataIndex: 'confidence',
              width: 100,
              render: (value) => `${Math.round((value || 0) * 100)}%`,
            },
            { title: '技能标签', dataIndex: 'skill_tags', width: 220, render: (value) => <SkillTags skills={value} /> },
            {
              title: '匹配分',
              width: 180,
              render: (_, record) => (
                <MatchScore score={resumeDetails[record.id]?.screening_report?.match_score} size="small" />
              ),
            },
            { title: '上传人', dataIndex: 'uploaded_by', width: 120, render: (value) => value || '-' },
            { title: '来源', dataIndex: 'source', width: 120 },
            {
              title: '创建时间',
              dataIndex: 'created_at',
              width: 180,
              render: (value) => dayjs(value).format('YYYY-MM-DD HH:mm'),
            },
            {
              title: '操作',
              fixed: 'right',
              width: 220,
              render: (_, record) => (
                <Space wrap>
                  <Button type="link" onClick={() => setSelected(record)}>
                    查看详情
                  </Button>
                  <Button type="link" loading={reparseLoadingId === record.id} onClick={() => void handleReparse(record)}>
                    重新解析
                  </Button>
                  <Button
                    type="link"
                    onClick={() => {
                      setScreeningRow(record);
                      screenForm.setFieldsValue({ position_name: '', job_requirements: '' });
                    }}
                  >
                    重新生成匹配报告
                  </Button>
                </Space>
              ),
            },
          ]}
          scroll={{ x: 1640 }}
        />
      </Card>
      <Drawer
        title={selected ? `${selected.original_filename} · 简历详情` : '简历详情'}
        width={900}
        open={!!selected}
        onClose={() => setSelected(null)}
        destroyOnClose
      >
        {!selected ? null : (
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="原始文件名">{selected.original_filename}</Descriptions.Item>
              <Descriptions.Item label="解析状态">
                <ResumeStatusTag status={selected.parse_status} />
              </Descriptions.Item>
              <Descriptions.Item label="上传人">{selected.uploaded_by || '-'}</Descriptions.Item>
              <Descriptions.Item label="来源">{selected.source}</Descriptions.Item>
              <Descriptions.Item label="置信度">{Math.round((selected.confidence || 0) * 100)}%</Descriptions.Item>
              <Descriptions.Item label="创建时间">{dayjs(selected.created_at).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
            </Descriptions>
            <ResumeInsightCard
              summary={selected.resume_summary}
              skills={selected.skill_tags}
              screeningReport={screeningReport || undefined}
              parseResult={parsedJson}
              warnings={selected.error_message ? [selected.error_message] : []}
            />
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="候选人姓名">{candidateText('name')}</Descriptions.Item>
              <Descriptions.Item label="学历">{candidateText('education')}</Descriptions.Item>
              <Descriptions.Item label="学校">{candidateText('school')}</Descriptions.Item>
              <Descriptions.Item label="专业">{candidateText('major')}</Descriptions.Item>
              <Descriptions.Item label="毕业年份">{candidateText('graduation_year')}</Descriptions.Item>
              <Descriptions.Item label="工作年限">{candidateText('work_years')}</Descriptions.Item>
            </Descriptions>
            <Card title="项目经历" size="small">
              <JsonViewer data={parsedJson.project_experiences} />
            </Card>
            <Card title="工作经历" size="small">
              <JsonViewer data={parsedJson.work_experiences} />
            </Card>
            <Card title="原始 parsed_json" size="small">
              <JsonViewer data={selected.parsed_json} />
            </Card>
          </Space>
        )}
      </Drawer>
      <Modal
        title="重新生成匹配报告"
        open={!!screeningRow}
        onCancel={() => setScreeningRow(null)}
        onOk={async () => {
          if (!screeningRow) {
            return;
          }
          const values = await screenForm.validateFields();
          await screenResume(screeningRow.id, values);
          messageApi.success('岗位匹配报告已重新生成。');
          setScreeningRow(null);
          await load();
        }}
      >
        <Form form={screenForm} layout="vertical">
          <Form.Item
            name="position_name"
            label="应聘岗位"
            rules={[{ required: true, message: '请输入岗位名称' }]}
          >
            <Input placeholder="例如：AI Agent开发实习生" />
          </Form.Item>
          <Form.Item name="job_requirements" label="岗位要求">
            <TextArea rows={4} placeholder="例如：熟悉 Python、FastAPI、RAG、Agent 和数据库设计" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
