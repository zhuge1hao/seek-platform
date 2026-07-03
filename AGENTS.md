# Project Agent Rules

项目根目录：`E:\USE\codexhome\agents-cowork\meizhaiseek-platform`

GitHub：`https://github.com/zhuge1hao/seek-platform.git`

接手时必须先读磁盘代码和文档，不要只依赖历史对话、Git 状态或记忆。

## 项目运行命令

一键启动开发服务：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

后端单独启动：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
```

前端单独启动：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run dev -- -p 3000
```

本地视频拆解 Agent 默认地址：

```text
http://127.0.0.1:8001
```

Docker 内访问宿主机 8001 时使用：

```text
http://host.docker.internal:8001
```

## 测试和校验命令

每次改动后至少运行：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
python -m compileall apps/api
python -m unittest discover -s apps/api/tests
cd apps\web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run build
```

基础 smoke：

```powershell
python apps/api/scripts/smoke_minimal.py
```

如果 smoke 缺 admin 凭据，设置：

```powershell
$env:SMOKE_ADMIN_USERNAME='admin'
$env:SMOKE_ADMIN_PASSWORD='<local-password>'
```

视频 Agent E2E：

```powershell
python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent
```

健康检查：

- `GET http://127.0.0.1:8000/health` 返回 `{"status":"ok","service":"meizhaiseek-api"}`。
- 登录后 `/api/admin/runtime/health` 返回当前版本。
- `/api/agents/video-script/status` 在 8001 可达时返回 connected，不可达时返回 disconnected，不能 500。

## 代码风格

- 复用现有 Next.js App Router、TypeScript、Tailwind、FastAPI、Pydantic、sqlite3 写法。
- 前端 HTTP 统一走 `apps/web/src/lib/api.ts`。
- SWR 只用于 GET/list/detail 读取型接口；POST/PUT/DELETE、上传、下载、任务提交仍走显式 API，成功后 mutate。
- 后端优先复用 `routers`、`services`、`schemas`、`workflows`。
- JSON 使用 UTF-8 和 `ensure_ascii=False`。
- 手工编辑优先用 `apply_patch`，改动聚焦，不顺手重构无关模块。
- 不新增无请求依赖，不做 speculative abstraction。

## 前端约束

- 前端不能直连 local agent，只能调用平台后端 API。
- 后端任务状态是唯一事实来源，禁止前端伪造 completed。
- 会话数据必须来自后端；localStorage 只保存 active id，不保存完整 messages。
- `/agent` run 状态优先 SSE，失败后 polling fallback；SWR 不重复轮询 run summary/result。
- viewer 只读；admin/operator 可按权限提交任务，最终以后端权限为准。
- 保留导航文案“美宅BI”“万能美虾”。
- 保留品牌和模型名：`meizhaiseek`、`meizhaiseek 2.0`。
- 前端接口异常必须显示错误态，不能白屏。

## 后端约束

- 不新增 MySQL、PostgreSQL、Redis、MongoDB 或其他外部数据库。
- APP SQLite 和 RAG SQLite 必须分开：
  - APP SQLite：`apps/api/runtime/app/meizhaiseek.sqlite3`
  - RAG SQLite：`apps/api/runtime/rag/rag.sqlite3`
- 不把 embedding 合并进 APP SQLite。
- 所有业务 API 遵守登录鉴权、admin/operator/viewer 权限和 user_id 隔离。
- 任务、会话、文件、Dataset、Artifact、Debug Payload 必须按 user_id 隔离。
- DeepSeek API Key 只从后端环境变量读取，不进入前端、日志或审计。
- Connector disabled/missing、HTTP 不可达、local agent 未启动时必须明确 failed。
- Audit/Debug 不保存密码、token、secret、API key 或完整超大 prompt/answer/document。

## 重要目录说明

- `apps/web/src/app`：页面路由。
- `apps/web/src/components`：Agent、QA、Dataset、后台和通用 UI。
- `apps/web/src/lib`：API client、auth、query keys、agent registry。
- `apps/web/src/hooks`：SWR hooks、Agent Run SSE/polling hooks。
- `apps/api/routers`：HTTP API。
- `apps/api/schemas`：Pydantic 请求/响应模型。
- `apps/api/services`：存储、鉴权、Connector、Dataset、local agent、conversation、QA/RAG。
- `apps/api/workflows`：Agent workflow 分发。
- `apps/api/tests`：标准 unittest。
- `apps/api/runtime`：本地运行数据，不提交 Git。
- `apps/api/uploads`：上传文件，不提交 Git。
- `docs/CODEX_HANDOFF.md`：当前接手事实。
- `docs/NEXT_TASKS.md`：下一步优先级。
- `docs/CHANGELOG_CONTEXT.md`：跨窗口版本背景。

## 每次改动后的自检要求

1. 先读 `AGENTS.md`、`docs/CODEX_HANDOFF.md`、`docs/NEXT_TASKS.md`、`docs/CHANGELOG_CONTEXT.md`。
2. 检查磁盘代码、runtime 状态和 `git status`，不要假设默认状态。
3. 运行后端 compileall、unittest 和前端 build。
4. 涉及 API 时做真实 API smoke，不用 UI 状态替代后端执行。
5. 回归登录、角色权限、用户隔离、取消、重试、下载。
6. 涉及页面时检查 loading/error/empty、长文本、滚动和小屏显示。
7. 提交前确认不包含 `.env`、runtime DB、generated secrets、logs、uploads、models、node_modules、`.next`。

## 禁止事项

- 不要伪造任务执行状态。
- 不要只做前端假数据。
- 不要只做 UI 而跳过真实 API、持久化和错误回写。
- 不要破坏 v1.2 登录鉴权和用户隔离。
- 不要破坏 v1.3 Connector、Payload Preview、Debug Replay。
- 不要破坏 v1.4 管理员、审计、权限和滚动修复。
- 不要破坏 v1.5 Dataset、字段映射、清洗、导出和安全下载。
- 不要破坏 v1.5.2-v1.5.6 QA/RAG/知识库/诊断/流式问答。
- 不要破坏 v1.5.7 APP SQLite 迁移和 APP/RAG SQLite 分离。
- 不要破坏 v1.5.8 conversation 增量 upsert、Dataset SQLite、service_events。
- 不要破坏 v1.6+ 视频拆解智能体生产化、真实执行、artifact 闭环。
- 不要提交 `.env`、runtime、SQLite、uploads、models、logs、node_modules、`.next`。
