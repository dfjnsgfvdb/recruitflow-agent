import {
  Alert,
  Button,
  Card,
  Col,
  Form,
  Input,
  Row,
  Select,
  Space,
  Tabs,
  Typography,
  Upload,
  message as antdMessage,
} from 'antd';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';
import { useState } from 'react';
import { processAgentMessage } from '../api/agent';
import { uploadResume } from '../api/resumes';
import BusinessResultCard from '../components/BusinessResultCard';
import JsonViewer from '../components/JsonViewer';
import PageHeader from '../components/PageHeader';
import ProcessSteps from '../components/ProcessSteps';
import ResumeInsightCard from '../components/ResumeInsightCard';
import ResumeStatusTag from '../components/ResumeStatusTag';
import SourceTag from '../components/SourceTag';
import type { AgentProcessResponse } from '../types/agent';
import type { ResumeUploadResponse } from '../types/resume';

const { Dragger } = Upload;
const { TextArea } = Input;

const examples = {
  create:
    '候选人张三，电话13800138000，投递AI Agent开发实习生，本科，有RAG和Spring Boot项目经验，简历通过，来源Boss直聘。',
  interview: '张三安排明天下午3点一面，面试官李工，腾讯会议。',
  second: '张三一面通过，安排二面，时间2026-06-28 15:00，面试官王工，腾讯会议。',
  clarify: '李四下午面试。',
  reject: '张三技术能力不匹配，流程结束，标记淘汰。',
  query: 'AI Agent开发实习生这个岗位现在招聘进展怎么样？',
};

type FormValues = {
  sender?: string;
  source?: string;
  message?: string;
  position_name?: string;
  job_requirements?: string;
};

export default function AgentConsole() {
  const [form] = Form.useForm<FormValues>();
  const [loading, setLoading] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [agentResult, setAgentResult] = useState<AgentProcessResponse | null>(null);
  const [resumeResult, setResumeResult] = useState<ResumeUploadResponse | null>(null);
  const [messageApi, contextHolder] = antdMessage.useMessage();

  const submit = async () => {
    const values = await form.validateFields();
    const hasResume = fileList.length > 0 && fileList[0].originFileObj;
    const message = (values.message || '').trim();

    if (!hasResume && !message) {
      messageApi.warning('未上传简历时，至少需要输入一条 HR 招聘消息。');
      return;
    }

    setLoading(true);
    setAgentResult(null);
    setResumeResult(null);

    try {
      if (hasResume) {
        const formData = new FormData();
        formData.append('file', fileList[0].originFileObj as File);
        formData.append('sender', values.sender || 'HR小王');
        formData.append('source', values.source || 'WEB_DEMO');
        if (message) {
          formData.append('message', message);
        }
        if (values.position_name) {
          formData.append('position_name', values.position_name);
        }
        if (values.job_requirements) {
          formData.append('job_requirements', values.job_requirements);
        }
        const response = await uploadResume(formData);
        setResumeResult(response);
        if (response.success) {
          messageApi.success('简历已上传，系统已完成简历解析与候选人建档。');
        } else {
          messageApi.error(response.message || '简历解析失败');
        }
        return;
      }

      const response = await processAgentMessage({
        message,
        sender: values.sender,
        source: values.source,
      });
      setAgentResult(response);
      if (response.success) {
        messageApi.success('企业微信招聘消息已完成自动识别与建档。');
      } else {
        messageApi.error(response.message || '处理失败');
      }
    } catch {
      messageApi.error('请求失败，请检查后端服务是否启动。');
    } finally {
      setLoading(false);
    }
  };

  const clear = () => {
    form.resetFields();
    form.setFieldsValue({ sender: 'HR小王', source: 'WEB_DEMO', message: examples.create });
    setFileList([]);
    setAgentResult(null);
    setResumeResult(null);
  };

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

  const needConfirmation = agentResult?.executed_actions?.some((item) => item.need_confirmation);
  const currentStep = resumeResult
    ? resumeResult.resume_file?.parse_status === 'FAILED'
      ? 1
      : 4
    : agentResult?.need_clarification
      ? 1
      : needConfirmation
        ? 3
        : 4;

  const activeMessage = resumeResult?.message || agentResult?.message;

  return (
    <>
      {contextHolder}
      <PageHeader
        title="企业微信招聘消息处理台"
        description="模拟 HR 在企业微信、企业微信群或腾讯文档备注中产生的招聘沟通内容。AI Agent 会自动识别候选人、岗位、面试安排和流程状态，并在上传简历 PDF 时自动合并简历画像、岗位匹配报告和建议面试问题。"
      />
      <Row gutter={20}>
        <Col span={10}>
          <Card title="消息输入区" className="page-card">
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                sender: 'HR小王',
                source: 'WEB_DEMO',
                message: examples.create,
                position_name: 'AI Agent开发实习生',
              }}
            >
              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item name="source" label="消息来源">
                    <Select
                      options={[
                        { label: 'Web Demo', value: 'WEB_DEMO' },
                        { label: '企业微信群', value: 'WECOM_GROUP' },
                        { label: '企业微信私聊', value: 'WECOM_PRIVATE' },
                        { label: '腾讯文档备注', value: 'TENCENT_DOC' },
                      ]}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="sender" label="发送人">
                    <Input placeholder="HR小王" />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item label="上传候选人简历 PDF">
                <Dragger {...uploadProps}>
                  <Typography.Title level={5} style={{ marginBottom: 8 }}>
                    上传候选人简历 PDF
                  </Typography.Title>
                  <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    可选。上传后系统会自动解析简历并与 HR 消息合并建档，替代 HR 手工查看简历和维护腾讯文档。
                  </Typography.Paragraph>
                </Dragger>
              </Form.Item>
              <Form.Item name="position_name" label="应聘岗位">
                <Input placeholder="例如：AI Agent开发实习生" />
              </Form.Item>
              <Form.Item name="job_requirements" label="岗位要求">
                <TextArea
                  rows={4}
                  placeholder="可选。输入岗位要求后，系统会生成更准确的岗位匹配报告和建议面试问题。"
                />
              </Form.Item>
              <Form.Item name="message" label="原始招聘消息">
                <TextArea rows={8} placeholder="粘贴企业微信招聘沟通内容。若已上传简历，消息可选；若未上传简历，则至少输入一条 HR 备注。" />
              </Form.Item>
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Space>
                  <Button type="primary" size="large" loading={loading} onClick={submit}>
                    AI 解析并建档
                  </Button>
                  <Button size="large" onClick={clear}>
                    清空
                  </Button>
                </Space>
                <div className="scenario-buttons">
                  <Typography.Text type="secondary">示例场景</Typography.Text>
                  <Space wrap style={{ marginTop: 8 }}>
                    <Button onClick={() => form.setFieldValue('message', examples.create)}>新增候选人</Button>
                    <Button onClick={() => form.setFieldValue('message', examples.interview)}>安排一面</Button>
                    <Button onClick={() => form.setFieldValue('message', examples.second)}>面试通过并安排二面</Button>
                    <Button onClick={() => form.setFieldValue('message', examples.clarify)}>信息不足触发追问</Button>
                    <Button danger onClick={() => form.setFieldValue('message', examples.reject)}>
                      高风险淘汰确认
                    </Button>
                    <Button onClick={() => form.setFieldValue('message', examples.query)}>查询岗位进展</Button>
                  </Space>
                </div>
              </Space>
            </Form>
          </Card>
        </Col>
        <Col span={14}>
          <Card title="处理结果区" className="page-card">
            {!agentResult && !resumeResult ? (
              <div className="result-placeholder">
                <SourceTag source="WECOM_GROUP" />
                <Typography.Title level={4}>从企业微信消息与简历 PDF 到招聘台账自动更新</Typography.Title>
                <Typography.Paragraph type="secondary">
                  提交 HR 消息后，系统会展示 AI 抽取、状态机校验、工具执行、同步更新与看板刷新链路；上传 PDF 时，还会额外生成候选人画像、岗位匹配分与建议面试问题。
                </Typography.Paragraph>
                <ProcessSteps current={0} />
              </div>
            ) : (
              <Space direction="vertical" size={14} style={{ width: '100%' }}>
                <Alert type={(agentResult?.success ?? resumeResult?.success) ? 'success' : 'error'} showIcon message={activeMessage} />
                <ProcessSteps current={currentStep} />
                <BusinessResultCard agentResult={agentResult} resumeResult={resumeResult} />
                {resumeResult?.resume_file ? (
                  <>
                    <Alert
                      type={resumeResult.resume_file.parse_status === 'NEED_OCR' || resumeResult.resume_file.parse_status === 'NEED_REVIEW' ? 'warning' : 'info'}
                      showIcon
                      message="简历解析状态"
                      description={<ResumeStatusTag status={resumeResult.resume_file.parse_status} />}
                    />
                    <ResumeInsightCard
                      summary={resumeResult.resume_file.resume_summary}
                      skills={resumeResult.resume_file.skill_tags}
                      parseResult={resumeResult.resume_parse_result}
                      screeningReport={resumeResult.screening_report}
                      warnings={resumeResult.warnings}
                    />
                  </>
                ) : null}
                {agentResult?.need_clarification ? (
                  <Alert
                    type="warning"
                    showIcon
                    message="需要 HR 补充信息"
                    description={agentResult.agent_result.clarification_questions.join('；') || '请补充关键字段后再执行。'}
                  />
                ) : null}
                {needConfirmation ? (
                  <Alert
                    type="warning"
                    showIcon
                    message="该操作涉及高风险或异常状态流转"
                    description="系统已生成待确认动作，进入待办中心前不会直接修改候选人招聘状态。"
                  />
                ) : null}
                <Tabs
                  items={[
                    {
                      key: 'agent',
                      label: 'AI 抽取结果',
                      children: <JsonViewer data={resumeResult?.resume_parse_result || agentResult?.agent_result} />,
                    },
                    {
                      key: 'tools',
                      label: '工具执行结果',
                      children: (
                        <JsonViewer
                          data={
                            resumeResult
                              ? {
                                  candidate: resumeResult.candidate,
                                  resume_file: resumeResult.resume_file,
                                  screening_report: resumeResult.screening_report,
                                  warnings: resumeResult.warnings,
                                }
                              : agentResult?.executed_actions
                          }
                        />
                      ),
                    },
                    {
                      key: 'raw',
                      label: '原始 JSON',
                      children: <JsonViewer data={resumeResult || agentResult} />,
                    },
                  ]}
                />
              </Space>
            )}
          </Card>
        </Col>
      </Row>
    </>
  );
}
