# Codex Handoff

## 项目名称与当前版本

- 项目：meizhaiseek-platform
- 当前版本：meizhaiseek v1.7.1
- 版本名称：智能体蓝图与方法论配置中心
- 仓库：https://github.com/zhuge1hao/seek-platform.git
- 本地路径：`E:\USE\codexhome\agents-cowork\meizhaiseek-platform`
- 当前分支：main
- 最近提交：`dd1a9e9 fix: restore UI docs encoding`
- 当前未跟踪文件：`ARCHITECTURE_EVALUATION_REPORT.md`，仅作参考，未提交。

## 当前项目目标

meizhaiseek-platform 是面向电商经营场景的本地轻量 AI 工作台。当前目标是在不破坏已有鉴权、Dataset、Connector、Debug Payload、后台管理、QA/RAG 和视频拆解能力的前提下，把 Agent Blueprint 作为现有 Registry/Workflow/Connector 的配置描述层稳定下来，并继续守住 `/agent` 真实任务链路。

## 技术栈与启动方式

- 前端：Next.js 14 App Router、React 18、TypeScript、Tailwind CSS、SWR、lucide-react。
- 后端：FastAPI、Uvicorn、Pydantic、标准库 sqlite3、requests、asyncio.to_thread wrapper。
- 存储：APP SQLite 与 RAG SQLite 双 SQLite 架构。
- AI 对话：DeepSeek OpenAI-compatible Chat Completions，本地 `bge-small-zh` embedding。
- 视频 Agent：平台通过 Connector 调用本地 8001 `/health` 和 `/run`。

启动：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

验证：

```powershell
python -m compileall apps/api
python -m unittest discover -s apps/api/tests
python -m pytest apps/api/tests
cd apps\web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run build
```

## 关键目录结构

```text
apps/web/src/app                 # 页面路由
apps/web/src/components          # Agent、Chat、Dataset、Admin UI
apps/web/src/hooks               # SWR hooks、SSE/polling hooks
apps/web/src/lib                 # API client、queryKeys、auth
apps/api/routers                 # FastAPI routers
apps/api/services                # 存储、鉴权、任务、Connector、QA/RAG、artifact
apps/api/workflows               # Agent workflow
apps/api/tests                   # unittest
apps/api/scripts/smoke_minimal.py
apps/api/runtime                 # 本地运行数据，不提交
apps/api/uploads                 # 上传文件，不提交
docs                             # 当前交接、API、测试、运维文档
```

## 已完成版本记录

### v1.7：智能体蓝图与方法论配置中心

- 新增 Agent Blueprint SQLite 表、store、service、validator、import/export 和 seed service。
- 新增蓝图 CRUD、版本、校验、发布、回滚、复制、停用、废弃、测试用例、导入导出 API。
- 后台新增“智能体蓝图”管理页，采用紧凑 JSON 编辑和必要操作按钮。
- `/api/agents` 增加蓝图关联字段，无蓝图智能体显示 `unmanaged`。
- `POST /api/agent-runs` 仅在关联蓝图 disabled/deprecated 时拒绝新任务。
- 视频拆解智能体 seeded 为 `bp_video_script_breakdown` published 蓝图，继续使用现有 `video_script_workflow`、8001 Connector 和结果面板。
- 新增 `docs/AGENT_BLUEPRINTS.md` 和蓝图自动化测试。

### v1.6.4：视频拆解智能体真实成功链路验收与产物闭环

- 默认 Connector 指向 `http://127.0.0.1:8001`、`/health`、`/run`。
- 平台 payload 映射为本地视频 Agent 原生 `/run` payload。
- 真实调用 8001，completed 后标准化 result_json。
- 读取 shot_report，登记 Excel、JSON、图片、folder_manifest artifacts。
- Debug Payload 保存真实 request/response/error。
- 前端 VideoBreakdownResultPanel 展示真实 summary 和 artifact 列表。
- smoke 增加 `--video-agent-e2e` 与 `--require-video-agent`。

### v1.6.5：架构评估 P1-P3 二轮优化、回归测试与服务启动

- 扩大 SWR 读取层覆盖。
- 新增核心 unittest：auth、conversation、task_store、agent-runs API、video normalizer。
- legacy JSON fallback 默认关闭，runtime health 显示 `legacy_json_fallback_enabled`。
- 新增 Docker production compose。
- 新增 SQLite async wrapper 第一阶段。
- 新增 `GET /api/agent-runs/{run_id}/events` SSE，前端失败回退 polling。
- 增强 video-agent E2E smoke。
- 修复 `/agent` 视频结果 tab 闪屏和长文本 hover/横向滚动展示。
- 修复 active docs / README 乱码，并重启本地服务确认 `/agent` 200。

## 当前正在处理的问题

最近用户要求：生成新窗口可继续接手的上下文交接包，并落盘到 `docs/CODEX_HANDOFF.md`、`docs/NEXT_TASKS.md`、`docs/CHANGELOG_CONTEXT.md`、`AGENTS.md`。本轮不要继续写新功能。

上一轮刚处理的问题：

- 用户反馈 UI 又掉了。
- 检查到前端源码当前 build 通过，旧 dev log 中残留过 TSX 乱码编译错误。
- 重启服务后 API 8000、Web 3000 正常，`/agent` HTTP 200。
- active docs 和 README 已重写为 UTF-8。

## 最近一次用户明确要求

“请你为当前项目生成一个新窗口可继续接手的上下文交接包。不要继续写新功能，先只做总结和落盘。”

## 已经改过的关键文件

最近提交和工作涉及：

- `README.md`
- `AGENTS.md`
- `docs/CODEX_HANDOFF.md`
- `docs/NEXT_TASKS.md`
- `docs/CHANGELOG_CONTEXT.md`
- `docs/API.md`
- `docs/PRD.md`
- `docs/TODO.md`
- `docs/SMOKE_TESTS.md`
- `docs/TESTING.md`
- `docs/STORAGE_SQLITE.md`
- `docs/FRONTEND_DATA_LAYER.md`
- `docs/VIDEO_AGENT_SETUP.md`
- `docs/VIDEO_AGENT_E2E_CHECKLIST.md`

v1.6.4/v1.6.5 关键代码文件包括：

- `apps/api/routers/agent_runs.py`
- `apps/api/routers/admin_runtime.py`
- `apps/api/services/video_agent_payload_builder.py`
- `apps/api/services/video_breakdown_result_normalizer.py`
- `apps/api/services/local_agent_client.py`
- `apps/api/services/artifact_service.py`
- `apps/api/services/async_store_utils.py`
- `apps/api/scripts/smoke_minimal.py`
- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/web/src/components/VideoBreakdownResultPanel.tsx`
- `apps/web/src/hooks/useAgentRunEvents.ts`
- `apps/web/src/hooks/useAgentRunPolling.ts`
- `apps/web/src/lib/api.ts`

## 数据库/API/前端状态

数据库：

- APP SQLite 为平台运行数据主存储。
- RAG SQLite 保持知识库向量存储边界。
- `APP_LEGACY_JSON_FALLBACK=false` 默认关闭。
- runtime、uploads、logs、generated secrets 不提交 Git。

API：

- `/health` 返回 `meizhaiseek-api`。
- `/api/admin/runtime/health` 应返回 `version=v1.7.1`。
- `/api/agents/video-script/status` 能识别 8001 connected/disconnected。
- `/api/agent-runs/{run_id}/events` 提供 SSE 状态流，失败后前端回退 polling。

前端：

- 版本展示为 `meizhaiseek v1.7.1`。
- 模型名展示为 `meizhaiseek 2.0`。
- 左侧主导航保留“美宅BI”“万能美虾”。
- `/agent` 会话列表走 SWR，run 状态由 SSE/polling 处理。
- 视频拆解结果 tab 闪屏已修复，长文本支持 hover 查看和横向滚动。

## 已知 bug / 风险

- `smoke_minimal.py` 需要 admin 凭据环境变量；当前 `.env` 里没有 `SMOKE_ADMIN_PASSWORD` 或 `MEIZHAISEEK_ADMIN_INITIAL_PASSWORD` 时会按设计失败。
- 仓库根目录有未跟踪 `ARCHITECTURE_EVALUATION_REPORT.md`，不要误提交。
- `apps/api/api-8000.log.*`、`apps/web/web-3000.log.*` 是历史日志文件，如要治理应移动到 `apps/api/runtime/logs/archive/`，不要删除非空日志。
- `docs/archive/**` 是历史备份，可能保留旧内容，仅供追溯，不作为当前文档来源。

## 不能破坏的功能

- v1.2 登录鉴权、角色权限、用户隔离。
- v1.3 Connector、Payload Preview、Debug Replay。
- v1.4 管理员、审计、权限、SafeDrawer 和滚动修复。
- v1.5 Dataset、字段映射、清洗、导出、安全下载。
- v1.5.2-v1.5.6 QA/RAG/知识库/诊断/流式问答。
- v1.5.7 APP SQLite 迁移和 APP/RAG SQLite 分离。
- v1.5.8 conversation 增量 upsert、Dataset SQLite、service_events。
- v1.6+ 视频拆解智能体真实调用、result normalizer、artifact 闭环。
- `/agent` 会话持久化、路由恢复、取消、重试、下载。
- `/chat` 流式问答。

## 下一窗口必须优先读取的文件

1. `AGENTS.md`
2. `docs/CODEX_HANDOFF.md`
3. `docs/NEXT_TASKS.md`
4. `docs/CHANGELOG_CONTEXT.md`
5. `docs/API.md`
6. `docs/PRD.md`
7. `docs/STORAGE_SQLITE.md`
8. `docs/AGENT_PERFORMANCE_NOTES.md`
9. `apps/web/src/app/agent/page.tsx`
10. `apps/api/routers/agent_runs.py`
11. `apps/api/services/conversation_store.py`
12. `apps/api/services/task_store.py`
13. `apps/api/workflows/video_script_workflow.py`

## 新窗口启动提示词

请继续接手 `E:\USE\codexhome\agents-cowork\meizhaiseek-platform`。当前版本是 meizhaiseek v1.7.1，GitHub 仓库是 `https://github.com/zhuge1hao/seek-platform.git`。请先完整读取 `AGENTS.md`、`docs/CODEX_HANDOFF.md`、`docs/NEXT_TASKS.md`、`docs/CHANGELOG_CONTEXT.md`、`docs/API.md`、`docs/PRD.md`、`docs/STORAGE_SQLITE.md`、`docs/AGENT_BLUEPRINTS.md`、`docs/AGENT_PERFORMANCE_NOTES.md`，再读取相关代码，不要只依赖历史对话或 Git 状态。当前最优先回归 `/agent` 和 Agent Blueprint：任务提交后左侧聊天记录必须新增并持久保存；切换路由再回来任务和聊天不能消失；视频/脚本拆解智能体必须真实调用后端和 local agent；`bp_video_script_breakdown` 必须保持 published 且继续绑定现有 workflow/Connector/renderer；其他未完成智能体不要伪造成 published。不要破坏 v1.2-v1.7.1 已有鉴权、Connector、Debug、管理员、Dataset、QA/RAG、SQLite、视频拆解、SSE/polling 和蓝图能力。


## v1.7.1 交接重点

v1.7.1 已把蓝图中心补成发布闭环：结构化编辑、验证历史、测试运行历史、版本差异、发布门禁、输入/结果预览和 `/agent` 轻量摘要均已接入。继续接手时仍需优先保护 `/agent` 持久化、视频拆解真实 8001 链路、Connector、Debug Payload、Dataset、QA/RAG 和双 SQLite 架构。

