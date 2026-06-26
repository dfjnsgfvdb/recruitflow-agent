import { Alert, Card, Col, List, Row, Typography } from 'antd';
import MatchScore from './MatchScore';
import SkillTags from './SkillTags';
import type { ResumeParseResult, ResumeScreeningReport } from '../types/resume';

interface ResumeInsightCardProps {
  summary?: string | null;
  skills?: string[] | null;
  parseResult?: ResumeParseResult | null;
  screeningReport?: ResumeScreeningReport | null;
  warnings?: string[];
}

export default function ResumeInsightCard({
  summary,
  skills,
  parseResult,
  screeningReport,
  warnings = [],
}: ResumeInsightCardProps) {
  return (
    <Card title="简历画像与岗位匹配" className="page-card">
      {warnings.length > 0 ? (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message="解析提示"
          description={warnings.join('；')}
        />
      ) : null}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Typography.Title level={5}>简历摘要</Typography.Title>
          <Typography.Paragraph className="resume-summary-text">
            {summary || parseResult?.resume_summary || '暂无简历摘要'}
          </Typography.Paragraph>
        </Col>
        <Col span={24}>
          <Typography.Title level={5}>技能标签</Typography.Title>
          <SkillTags skills={skills || parseResult?.skills} />
        </Col>
        {screeningReport ? (
          <>
            <Col span={12}>
              <Typography.Title level={5}>岗位匹配分</Typography.Title>
              <MatchScore score={screeningReport.match_score} />
            </Col>
            <Col span={12}>
              <Typography.Title level={5}>匹配结论</Typography.Title>
              <Typography.Paragraph>{screeningReport.match_reason || '暂无匹配结论'}</Typography.Paragraph>
            </Col>
          </>
        ) : null}
        <Col span={8}>
          <Typography.Title level={5}>优势点</Typography.Title>
          <List
            size="small"
            dataSource={screeningReport?.strengths || parseResult?.strengths || []}
            locale={{ emptyText: '暂无优势点' }}
            renderItem={(item) => <List.Item>{item}</List.Item>}
          />
        </Col>
        <Col span={8}>
          <Typography.Title level={5}>风险点</Typography.Title>
          <List
            size="small"
            dataSource={screeningReport?.risks || parseResult?.risks || []}
            locale={{ emptyText: '暂无风险点' }}
            renderItem={(item) => <List.Item>{item}</List.Item>}
          />
        </Col>
        <Col span={8}>
          <Typography.Title level={5}>建议面试问题</Typography.Title>
          <List
            size="small"
            dataSource={screeningReport?.suggested_interview_questions || parseResult?.suggested_interview_questions || []}
            locale={{ emptyText: '暂无建议面试问题' }}
            renderItem={(item) => <List.Item>{item}</List.Item>}
          />
        </Col>
      </Row>
    </Card>
  );
}
