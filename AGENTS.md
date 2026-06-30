# Project Agent Rules

项目根目录：`E:\USE\codexhome\agents-cowork\meizhaiseek-platform`

当前仓库已初始化 Git，并已推送到 `https://github.com/zhuge1hao/seek-platform.git`。继续接手时仍必须先读磁盘代码和文档，不要只依赖历史对话或 Git 状态判断真实实现。

## 项目运行命令

一键开发启动：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

分开启动后端：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\api
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

分开启动前端：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\web
npm.cmd install
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run dev -- -p 3000
```

生产构建前端：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run build
npm.cmd run start -- -H 127.0.0.1 -p 3000
```

真实视频拆解 local agent 默认依赖：

```text
POST http://localhost:8001/api/agent/run
```

如果 8001 没有真实 local agent 服务，任务必须真实 failed，不能伪造成成功。

## 测试/校验命令

每次代码改动后至少运行：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
python -m compileall apps/api

cd apps\web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run build
```

涉及 API 时检查：

- `GET /health` 返回 `{"status":"ok","service":"meizhaiseek-api"}`。
- `/api/admin/runtime/health` 返回当前版本。
- `/api/admin/storage/health` admin 可访问，非 admin 返回 403，未登录返回 401。
- Agent Run 创建、查询、取消、重试必须是真实后端状态。
- 用户之间不能越权读取任务、会话、文件、Dataset、Artifact、Debug Payload。
- 下载路径必须通过安全目录和所有权校验。

## 代码风格

- 延续现有 Next.js App Router、TypeScript、Tailwind、FastAPI、Pydantic、sqlite3 写法。
- 优先复用现有 routers、services、schemas、workflows、components。
- 前端接口统一走 `apps/web/src/lib/api.ts`。
- 后端 JSON 使用 UTF-8 和 `ensure_ascii=False`。
- 手工编辑使用 `apply_patch`，改动聚焦，不顺手重构无关模块。
- 不新增无请求依赖，不做 speculative abstraction。

## 前端约束

- 前端不能直连具体 local agent，只能调用平台后端 API。
- 后端任务状态是唯一事实来源；禁止前端伪造 `completed` 或成功结果。
- 会话数据必须来自后端，localStorage 只存 active ID，不存完整 messages。
- 长列表、抽屉、弹窗保持独立滚动、小屏适配、loading/error/empty 状态。
- viewer 只读；admin/operator 可按权限提交任务，最终以后端权限为准。
- 保留 `meizhaiseek`、`meizhaiseek 2.0`、“美宅BI”、“万能美虾”。
- 不恢复旧品牌词、用户额度文案、旧历史 mock 或开发期文案。

## 后端约束

- 不新增 MySQL/PostgreSQL/Redis/MongoDB。
- APP SQLite 和 RAG SQLite 必须分开：
  - APP SQLite：`apps/api/runtime/app/meizhaiseek.sqlite3`
  - RAG SQLite：`apps/api/runtime/rag/rag.sqlite3`
- 不把 RAG embedding 合并进 APP SQLite。
- 所有业务 API 遵守 v1.2 鉴权、admin/operator/viewer 权限和 user_id 隔离。
- 任务、会话、文件、Dataset、Artifact、Debug Payload 必须按 user_id 隔离。
- DeepSeek API Key 只从后端环境变量读取，不进前端、日志或审计。
- Connector disabled/missing、HTTP 不可达、本地 agent 未启动时必须明确 failed。
- Audit/Debug 不保存密码、token、secret、API key、完整 prompt、完整 answer、完整大文档内容。

## 重要目录说明

- `apps/web/src/app`：页面路由。
- `apps/web/src/components`：Agent、QA、Dataset、后台和通用 UI。
- `apps/web/src/lib`：API client、auth、agent registry/fallback、性能探针。
- `apps/web/src/hooks`：前端 hook，例如 agent run 单一轮询。
- `apps/api/routers`：HTTP API。
- `apps/api/schemas`：Pydantic 请求/响应模型。
- `apps/api/services`：存储、鉴权、Connector、Dataset、local agent、conversation、QA/RAG。
- `apps/api/workflows`：orchestrator 分发目标 workflow。
- `apps/api/runtime/app`：APP SQLite，本地运行数据，不提交 Git。
- `apps/api/runtime/rag`：RAG SQLite，本地知识库数据，不提交 Git。
- `apps/api/runtime/legacy_json_backups`：旧 JSON 备份，不提交 Git。
- `docs/CODEX_HANDOFF.md`：当前事实、风险和接手说明。
- `docs/NEXT_TASKS.md`：下一步任务优先级和验收标准。
- `docs/CHANGELOG_CONTEXT.md`：跨窗口变更背景。

## 每次改动后的自检要求

1. 先读 `AGENTS.md`、`docs/CODEX_HANDOFF.md`、`docs/NEXT_TASKS.md`、`docs/CHANGELOG_CONTEXT.md`。
2. 直接检查磁盘文件、runtime 状态和当前 Git 状态，不假定默认状态。
3. 运行后端编译和前端构建。
4. 对变更主流程做真实 API smoke，不用 UI 状态替代后端执行。
5. 回归登录、角色权限、用户隔离、取消、重试、下载。
6. 涉及页面时检查滚动、横向溢出、弹窗层级、loading/error/empty。
7. 涉及文档时扫描旧品牌词和禁用文案。

## 禁止事项

- 不伪造任务执行状态。
- 不把前端假数据当作后端成功。
- 不只做前端 UI 而跳过真实 API、持久化和错误回写。
- 不破坏 v1.2 登录鉴权和用户隔离。
- 不破坏 v1.3 Connector、Payload Preview、Debug Replay。
- 不破坏 v1.4 管理员、审计、权限、SafeDrawer 和滚动修复。
- 不破坏 v1.5 Dataset、字段映射、清洗、导出和安全下载。
- 不破坏 v1.5.2-v1.5.6 QA/RAG/知识库/诊断/流式问答。
- 不破坏 v1.5.7 APP SQLite 迁移和 APP/RAG SQLite 分离。
- 不破坏 v1.5.8 conversation 增量 upsert、Dataset SQLite、service_events。
- 不破坏 v1.6 视频拆解智能体生产化能力。
- 不让前端直连 local agent。
- 不开放任意本地路径下载。
- 不恢复旧品牌、用户额度展示或旧导航文案。
- 不提交 `.env`、runtime、SQLite、uploads、models、logs、node_modules、`.next`。
