# RecruitFlow Agent Frontend

RecruitFlow Agent Frontend 是招聘流程自动化 Demo 的前端工作台，基于 React + Vite + TypeScript + Ant Design + ECharts 构建，用于展示 AI 招聘消息处理、招聘看板、候选人列表、待确认动作和 AI 处理日志。

## 技术栈

- React
- Vite
- TypeScript
- Ant Design
- Axios
- React Router
- ECharts / echarts-for-react
- dayjs

## 安装依赖

```bash
cd frontend
npm install
```

如果 PowerShell 禁止执行 `npm.ps1`，可使用：

```powershell
npm.cmd install
```

## 配置 .env

```bash
copy .env.example .env
```

默认配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

如果后端部署在其他地址，修改 `VITE_API_BASE_URL` 即可。

## 启动命令

```bash
npm run dev
```

PowerShell 可使用：

```powershell
npm.cmd run dev
```

访问地址：

```text
http://localhost:5173
```

## 页面说明

- `AI 消息处理`：输入 HR 自然语言招聘消息，调用 `/api/agent/process-message`，展示 AI 抽取 JSON 和工具执行结果。
- `招聘看板`：展示候选人总数、今日新增、待面试、Offer 阶段、超时未跟进，并展示阶段/岗位图表。
- `候选人列表`：展示候选人数据，支持前端搜索和 Drawer 查看完整 JSON。
- `待确认动作`：展示高风险 pending action，支持确认执行和拒绝。
- `AI 处理日志`：展示 recruitment events，支持查看模型抽取结果。

## 后端接口依赖

前端依赖以下 FastAPI 接口：

- `POST /api/agent/process-message`
- `GET /api/candidates`
- `GET /api/interviews`
- `GET /api/events`
- `GET /api/dashboard/summary`
- `GET /api/confirmations/pending`
- `POST /api/confirmations/{pending_action_id}/approve`
- `POST /api/confirmations/{pending_action_id}/reject`

请先启动后端：

```powershell
cd backend
python run.py
```

后端需要允许 CORS 来源 `http://localhost:5173`。当前后端 Demo 已默认允许该来源；如果请求被浏览器拦截，请检查 FastAPI CORS 配置。

## 演示流程

1. 打开 `AI 消息处理` 页面。
2. 点击“新增候选人”示例，提交后可在 `候选人列表` 和 `AI 处理日志` 查看结果。
3. 点击“安排一面”示例，提交后可在看板看到待面试数据变化。
4. 点击“淘汰候选人”示例，系统会生成待确认动作。
5. 进入 `待确认动作` 页面，点击“确认执行”后候选人状态才会真正变更。
6. 进入 `AI 处理日志` 页面查看 NEED_CONFIRMATION、SUCCESS、FAILED 等事件记录。
