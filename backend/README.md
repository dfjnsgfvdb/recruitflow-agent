# RecruitFlow Agent

RecruitFlow Agent 是一个 AI 招聘流程自动化后端 Demo。它接收 HR 的自然语言招聘消息，通过 `MockRecruitmentAgent` 模拟 AI Agent 抽取候选人、面试和阶段流转信息，并将候选人、面试、招聘事件日志写入 MySQL，同时提供招聘看板接口。

当前版本不接真实大模型、不接真实企业微信、不接真实腾讯文档，外部集成都用 Mock 实现，保证没有 API Key 也能跑通完整流程。

## 技术栈

- Python
- FastAPI
- Uvicorn
- SQLAlchemy ORM
- MySQL
- PyMySQL
- Pydantic / pydantic-settings
- python-dotenv

## MySQL 建库 SQL

```sql
CREATE DATABASE IF NOT EXISTS recruitflow_agent
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
```

## 安装依赖

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux 激活虚拟环境：

```bash
source .venv/bin/activate
```

## 配置 .env

```bash
cd backend
copy .env.example .env
```

按本地 MySQL 修改 `.env`：

```env
APP_NAME=RecruitFlow Agent
APP_ENV=dev
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=recruitflow_agent
```

## 启动命令

```bash
cd backend
python run.py
```

服务默认启动在：

```text
http://localhost:8000
```

接口文档：

```text
http://localhost:8000/docs
```

应用启动时会执行 `Base.metadata.create_all(bind=engine)` 自动创建表。请先确保 MySQL 已启动且数据库已创建。

## 测试接口

健康检查：

```bash
curl http://localhost:8000/health
```

创建或更新候选人：

```bash
curl -X POST http://localhost:8000/api/agent/process-message ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"候选人张三通过Boss直聘投递AI Agent开发实习生，本科，清华大学，手机号13800138000\",\"sender\":\"HR小王\",\"source\":\"WEB_DEMO\"}"
```

安排面试：

```bash
curl -X POST http://localhost:8000/api/agent/process-message ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"安排张三AI Agent开发实习生一面，时间2026-06-26 14:00，面试官李经理，地点A101\"}"
```

触发追问：

```bash
curl -X POST http://localhost:8000/api/agent/process-message ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"李四下午面试\"}"
```

查看看板：

```bash
curl http://localhost:8000/api/dashboard/summary
```

查看候选人列表：

```bash
curl http://localhost:8000/api/candidates
```

查看面试列表：

```bash
curl http://localhost:8000/api/interviews
```

查看事件日志：

```bash
curl http://localhost:8000/api/events
```

## 示例请求

```json
{
  "message": "候选人张三通过Boss直聘投递AI Agent开发实习生，本科，清华大学，手机号13800138000",
  "sender": "HR小王",
  "source": "WEB_DEMO"
}
```

示例响应会包含：

- `agent_result`：Mock Agent 抽取出的意图、候选人、面试和动作。
- `executed_actions`：工具层实际执行的数据库操作和 Mock 同步结果。
- `need_clarification`：是否需要 HR 补充信息。

## 项目目录说明

```text
backend/
├── app/
│   ├── main.py                  # FastAPI 应用入口、CORS、路由注册、自动建表
│   ├── core/config.py           # pydantic-settings 环境变量配置
│   ├── db/database.py           # SQLAlchemy engine、SessionLocal、Base、get_db
│   ├── db/models.py             # Position、Candidate、Interview、RecruitmentEvent、SyncLog
│   ├── schemas/                 # 请求响应 Pydantic Schema
│   ├── services/                # 候选人、面试、事件、看板服务层
│   ├── agents/recruitment_agent.py
│   │                            # MockRecruitmentAgent 规则解析
│   ├── tools/                   # 工具执行器和企业微信/腾讯文档 Mock
│   └── api/routers/             # HTTP API 路由
├── requirements.txt
├── .env.example
├── README.md
└── run.py
```

## 当前限制

- `MockRecruitmentAgent` 使用正则和关键词规则，不调用真实大模型。
- `wecom_mock` 和 `tencent_doc_mock` 只返回模拟结果，并写入 `sync_logs`。
- 面试时间仅支持 `YYYY-MM-DD`、`YYYY-MM-DD HH:mm`、`YYYY-MM-DD HH:mm:ss` 格式，无法解析“明天下午”等自然语言时间。

## 企业级增强能力

本阶段围绕 HR 日常在企业微信、企业微信群和腾讯在线文档中手工记录招聘数据的痛点，增加低成本可运行的企业级增强能力：

- 批量处理企业微信群消息：支持多行粘贴，一行一条独立解析和执行。
- 超时未跟进提醒：识别超过 48 小时未更新的候选人。
- 面试反馈超时提醒：识别面试结束超过 24 小时仍未反馈的记录。
- 腾讯文档/企业微信同步日志：通过 `sync_logs` 暴露 Mock 同步状态。
- 数据质量检查：识别缺手机号、缺岗位、缺面试官等结构化数据问题。
- 低置信度 AI 解析追踪：聚合 `confidence < 0.7` 的事件。
- 疑似重复候选人识别：按手机号或姓名+岗位聚合重复记录。

### 批量处理企业微信群消息

```bash
curl -X POST http://localhost:8000/api/agent/process-batch ^
  -H "Content-Type: application/json" ^
  -d "{\"raw_text\":\"HR小王：候选人张三，电话13800138000，投递AI Agent开发实习生，简历通过\nHR小李：李四下午面试。\nHR小王：王五技术不匹配，流程结束，标记淘汰。\",\"source\":\"WECOM_GROUP\",\"default_sender\":\"HR小王\"}"
```

说明：

- 系统按换行拆分消息。
- 支持 `发送人：内容` 和 `发送人: 内容`。
- 单条失败不会影响其他消息。
- 每条消息都会复用单条 Agent 处理链路并写入事件日志。

### 查询待办提醒

```bash
curl http://localhost:8000/api/tasks/reminders
```

返回：

- `overdue_candidates`：超过 48 小时未跟进候选人。
- `upcoming_interviews`：未来 24 小时内待面试。
- `interview_feedback_overdue`：面试结束超过 24 小时仍未反馈。
- `offer_followup_overdue`：Offer 已发超过 3 天未跟进。

### 查询同步日志

```bash
curl http://localhost:8000/api/sync-logs
```

返回最近 100 条腾讯文档和企业微信 Mock 同步记录。

### 查询数据质量

```bash
curl http://localhost:8000/api/data-quality/summary
```

返回：

- `missing_phone_candidates`
- `missing_position_candidates`
- `missing_interviewer_interviews`
- `low_confidence_events`
- `duplicate_candidate_groups`

### Dashboard 增强统计

`GET /api/dashboard/summary` 已增加：

- `pending_confirmation_count`
- `overdue_candidate_count`
- `upcoming_interview_count`
- `sync_success_count`
- `sync_failed_count`
- `low_confidence_event_count`

## 第 3 步：真实 LLM Agent 抽取

项目现在支持通过 OpenAI-compatible API 调用真实模型完成招聘消息结构化抽取。业务层仍然只依赖统一的 Agent 抽象：

- `LLM_PROVIDER=mock`：使用本地规则版 `MockRecruitmentAgent`，不需要 API Key。
- `LLM_PROVIDER=openai`：使用 OpenAI SDK 默认地址或自定义 `LLM_BASE_URL`。
- `LLM_PROVIDER=qwen`：使用 OpenAI-compatible 协议，请配置通义千问兼容接口的 `LLM_BASE_URL`。
- `LLM_PROVIDER=deepseek`：使用 OpenAI-compatible 协议，请配置 DeepSeek 兼容接口的 `LLM_BASE_URL`。

新增依赖：

```bash
pip install -r requirements.txt
```

### mock 模式

```env
LLM_PROVIDER=mock
LLM_FALLBACK_TO_MOCK=true
```

### OpenAI 模式

```env
LLM_PROVIDER=openai
LLM_API_KEY=你的 API Key
LLM_BASE_URL=
LLM_MODEL=gpt-4.1-mini
LLM_TEMPERATURE=0
LLM_TIMEOUT_SECONDS=30
LLM_FALLBACK_TO_MOCK=true
```

### Qwen 模式

```env
LLM_PROVIDER=qwen
LLM_API_KEY=你的 API Key
LLM_BASE_URL=你的 OpenAI-compatible Base URL
LLM_MODEL=你的模型名
LLM_TEMPERATURE=0
LLM_TIMEOUT_SECONDS=30
LLM_FALLBACK_TO_MOCK=true
```

### DeepSeek 模式

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=你的 API Key
LLM_BASE_URL=你的 OpenAI-compatible Base URL
LLM_MODEL=你的模型名
LLM_TEMPERATURE=0
LLM_TIMEOUT_SECONDS=30
LLM_FALLBACK_TO_MOCK=true
```

如果真实模型调用失败，且 `LLM_FALLBACK_TO_MOCK=true`，接口会自动降级到 Mock Agent，避免招聘流程接口崩溃。

### 第 3 步测试样例

测试 1：候选人创建

```bash
curl -X POST http://localhost:8000/api/agent/process-message ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"候选人张三，电话13800138000，投递AI Agent开发实习生，本科，有RAG和Spring Boot项目经验，简历通过，来源Boss直聘。\",\"sender\":\"HR小王\",\"source\":\"WEB_DEMO\"}"
```

期望：

- `intent = CREATE_CANDIDATE`
- 创建候选人
- `stage = RESUME_PASSED`
- 写入 `recruitment_events`

测试 2：安排面试

```bash
curl -X POST http://localhost:8000/api/agent/process-message ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"张三安排明天下午3点一面，面试官李工，腾讯会议。\",\"sender\":\"HR小王\",\"source\":\"WEB_DEMO\"}"
```

期望：

- `intent = SCHEDULE_INTERVIEW`
- 创建面试
- `stage = FIRST_INTERVIEW_PENDING`

测试 3：信息不足追问

```bash
curl -X POST http://localhost:8000/api/agent/process-message ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"李四下午面试。\",\"sender\":\"HR小王\",\"source\":\"WEB_DEMO\"}"
```

期望：

- `need_clarification = true`
- 不创建候选人和面试
- 写入 `NEED_CLARIFICATION` 事件

测试 4：淘汰候选人

```bash
curl -X POST http://localhost:8000/api/agent/process-message ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"王五技术能力不匹配，流程结束，标记淘汰。\",\"sender\":\"HR小王\",\"source\":\"WEB_DEMO\"}"
```

期望：

- `intent = REJECT_CANDIDATE`
- `risk_level = HIGH`
- `stage = REJECTED`

## 第 4 步：工具调用安全增强

第 4 步增加了 Agent actions 的执行安全机制。LLM 或 Mock Agent 仍然只负责输出结构化 `agent_result`，真正执行由 `RecruitmentToolExecutor` 完成。执行前会经过字段完整性校验、招聘状态机校验、系统内置风险策略和高风险确认机制。

### 状态机校验

招聘阶段不能任意跳转。例如候选人应该从 `RESUME_PASSED` 进入 `FIRST_INTERVIEW_PENDING`，再进入后续阶段。模型输出的 `stage_change.new_stage` 不能直接信任，必须经过状态机。

示例合法流转：

```text
NEW -> SCREENING / RESUME_PASSED / RESUME_REJECTED
RESUME_PASSED -> FIRST_INTERVIEW_PENDING
FIRST_INTERVIEW_PENDING -> FIRST_INTERVIEW_PASSED / FIRST_INTERVIEW_REJECTED / REJECTED
FIRST_INTERVIEW_PASSED -> SECOND_INTERVIEW_PENDING
SECOND_INTERVIEW_PENDING -> SECOND_INTERVIEW_PASSED / REJECTED
SECOND_INTERVIEW_PASSED -> OFFER_PENDING
OFFER_PENDING -> OFFER_SENT
OFFER_SENT -> HIRED / REJECTED
```

如果发生状态跳跃或回退，系统不会直接改候选人状态，而是创建待确认动作。

### 高风险动作确认

系统内置风险策略优先于模型输出，不能完全信任 LLM 的 `risk_level`。

低风险动作会自动执行：

- `create_candidate`
- `sync_to_tencent_doc`
- `send_wecom_notice`
- `query_dashboard`
- `ask_clarification`

中风险动作需要先通过状态机校验：

- `update_candidate_stage`
- `create_interview`
- `add_interview_feedback`

高风险动作必须进入待确认队列：

- `reject_candidate`
- `send_offer`
- `mark_hired`

### pending_actions 表

`pending_actions` 表保存所有需要 HR 确认的动作，包括：

- 候选人 ID
- 动作类型
- 风险等级
- 模型抽取 payload
- 进入确认的原因
- 请求人和确认人
- 当前状态：`PENDING`、`APPROVED`、`REJECTED`、`EXECUTED`、`FAILED`

只有 HR 调用确认接口后，高风险动作才会真正修改候选人主数据。

### 第 4 步测试

测试 1：正常新增候选人

```bash
curl -X POST http://localhost:8000/api/agent/process-message ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"候选人张三，电话13800138000，投递AI Agent开发实习生，本科，有RAG项目经验，简历通过，来源Boss直聘。\",\"sender\":\"HR小王\",\"source\":\"WEB_DEMO\"}"
```

期望：

- 自动创建候选人
- `executed_actions` 包含 `create_candidate`
- 不需要 `pending_action`

测试 2：正常安排一面

```bash
curl -X POST http://localhost:8000/api/agent/process-message ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"张三安排明天下午3点一面，面试官李工，腾讯会议。\",\"sender\":\"HR小王\",\"source\":\"WEB_DEMO\"}"
```

期望：

- 如果张三当前状态允许进入 `FIRST_INTERVIEW_PENDING`，则自动创建面试
- 如果状态不允许，则创建 `pending_action`

测试 3：淘汰候选人

```bash
curl -X POST http://localhost:8000/api/agent/process-message ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"张三技术能力不匹配，流程结束，标记淘汰。\",\"sender\":\"HR小王\",\"source\":\"WEB_DEMO\"}"
```

期望：

- 不直接修改张三 `stage`
- 创建 `pending_action`
- `GET /api/confirmations/pending` 可以查到

查询待确认动作：

```bash
curl http://localhost:8000/api/confirmations/pending
```

测试 4：确认淘汰

```bash
curl -X POST http://localhost:8000/api/confirmations/1/approve ^
  -H "Content-Type: application/json" ^
  -d "{\"approved_by\":\"HR负责人\"}"
```

期望：

- 张三 `stage` 变为 `REJECTED`
- `pending_action.status` 变为 `EXECUTED`
- `recruitment_events` 写入 `SUCCESS`

测试 5：拒绝高风险动作

```bash
curl -X POST http://localhost:8000/api/confirmations/1/reject ^
  -H "Content-Type: application/json" ^
  -d "{\"approved_by\":\"HR负责人\",\"reason\":\"暂时继续观察，不淘汰\"}"
```

期望：

- `pending_action.status` 变为 `REJECTED`
- 候选人 `stage` 不变

### 统一工具执行结果

`executed_actions` 现在统一返回 `ToolExecutionResult`：

```json
{
  "tool": "reject_candidate",
  "success": true,
  "status": "NEED_CONFIRMATION",
  "message": "已生成待确认任务。",
  "data": {"candidate_id": 1},
  "risk_level": "HIGH",
  "need_confirmation": true,
  "pending_action_id": 1,
  "error_message": null
}
```

## 简历 PDF 解析能力

RecruitFlow Agent 现在支持在候选人建档流程中上传简历 PDF，并将“HR 招聘消息 + 简历附件”合并成结构化候选人档案。

核心能力：

1. 支持上传 PDF 简历，文件限制 10MB，只保存重命名后的安全文件名。
2. 使用 `pypdf` 优先抽取文本，文本不足时使用 `pdfplumber` 兜底。
3. 暂不引入 OCR；扫描件或不可抽取文本的 PDF 会标记为 `NEED_OCR`。
4. 支持 Mock / OpenAI-compatible / Qwen / DeepSeek 简历结构化解析。
5. 自动抽取学历、学校、专业、毕业年份、工作年限、技能、项目经历、证书、简历摘要、优势点、风险点和建议面试问题。
6. 支持 HR 消息与简历联合建档，HR 消息中的岗位、阶段、来源优先，简历中的履历字段优先。
7. 如果 HR 消息和简历中的手机号或邮箱冲突，会标记为 `NEED_REVIEW`，避免自动覆盖关键联系方式。
8. 自动生成岗位匹配报告，包括匹配分、匹配等级、优势、风险、缺失要求和建议面试问题。
9. 写入 `resume_files`、`resume_screening_reports`、`recruitment_events` 和 `sync_logs`，方便审计和同步展示。
10. 企业版可以继续接入 OCR、对象存储、企业微信附件回调和腾讯文档真实 API。

### 简历接口

- `POST /api/resumes/upload`：上传并解析简历 PDF。
- `GET /api/resumes`：查看最近上传的简历。
- `GET /api/resumes/{resume_id}`：查看简历详情。
- `GET /api/candidates/{candidate_id}/resume`：查看候选人最新简历和筛选报告。
- `POST /api/resumes/{resume_id}/reparse`：重新解析简历。
- `POST /api/resumes/{resume_id}/screen`：按新的岗位要求重新生成筛选报告。

### 上传简历 curl 示例

```bash
curl -X POST http://127.0.0.1:8000/api/resumes/upload \
  -F "file=@张三简历.pdf" \
  -F "message=候选人张三，投递AI Agent开发实习生，简历通过，来源Boss直聘。" \
  -F "sender=HR小王" \
  -F "source=WECOM_GROUP" \
  -F "position_name=AI Agent开发实习生" \
  -F "job_requirements=熟悉Python、FastAPI、RAG、Agent和后端数据库设计"
```

### 重新筛选 curl 示例

```bash
curl -X POST http://127.0.0.1:8000/api/resumes/1/screen \
  -H "Content-Type: application/json" \
  -d '{"position_name":"AI Agent开发实习生","job_requirements":"熟悉Python、FastAPI、RAG、Agent、MySQL"}'
```

### 数据质量增强

`GET /api/data-quality/summary` 已增加简历相关问题：

- `candidates_without_resume`：没有上传简历的候选人。
- `resume_parse_failed`：解析失败的简历。
- `resume_need_ocr`：疑似扫描件，需要 OCR 的简历。
- `resume_need_review`：需要人工复核的简历。
- `contact_conflicts`：HR 消息与简历联系方式冲突。
- `low_match_score_but_resume_passed`：简历通过但匹配分低于 60 的候选人。

> 注意：如果你是在已有数据库上升级，应用启动时会尝试自动补齐 `candidates` 表的简历字段。生产环境建议改用 Alembic 管理数据库迁移。
