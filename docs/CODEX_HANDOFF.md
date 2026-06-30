# Codex Handoff

## 项目名称与当前版本

- 项目：`meizhaiseek-platform`
- 当前版本：`meizhaiseek v1.6.3`
- 版本名称：架构评估 P1-P3 优化与工程规范补齐
- 项目路径：`E:\USE\codexhome\agents-cowork\meizhaiseek-platform`
- GitHub：`https://github.com/zhuge1hao/seek-platform.git`
- 当前分支：`main`
- 最近提交：本轮提交 `chore: optimize architecture P1-P3 items`

## 当前项目目标

meizhaiseek 是面向电商经营全链路的 AI 平台。当前目标是在不破坏已有鉴权、RAG、Dataset、Connector、Debug Payload、后台管理能力的前提下，继续稳定 `/chat` 流式问答、`/agent` 智能体任务、视频拆解智能体、APP SQLite 运行数据存储和 RAG SQLite 知识库边界。

## 技术栈与启动方式

- 前端：Next.js 14 App Router、React 18、TypeScript、Tailwind CSS、lucide-react。
- 后端：FastAPI、Uvicorn、Pydantic、requests、标准库 `sqlite3`。
- AI 问答：DeepSeek OpenAI-compatible Chat Completions，支持非流式和 SSE 流式。
- Embedding：本地 `bge-small-zh`，通过 `sentence-transformers` 懒加载。
- 主存储：APP SQLite，路径 `apps/api/runtime/app/meizhaiseek.sqlite3`。
- RAG 存储：独立 SQLite，路径 `apps/api/runtime/rag/rag.sqlite3`。
- 本地视频 agent：默认 `http://127.0.0.1:8001`，平台不能伪造成功。

启动：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

校验：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
python -m compileall apps/api

cd apps\web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run build
```

## 关键目录结构

```text
apps/api/
  main.py
  routers/
    agent_runs.py
    conversations.py
    qa_chat.py
    qa_knowledge.py
    admin_runtime.py
  services/
    app_sqlite.py
    app_sqlite_migrations.py
    json_to_sqlite_migrator.py
    task_store.py
    conversation_store.py
    qa_conversation_store.py
    dataset_store.py
    service_events.py
    video_agent_status_service.py
  workflows/
    video_script_workflow.py
  runtime/              # 本地运行数据，不提交 Git
apps/web/src/
  app/
    agent/page.tsx
    chat/page.tsx
  components/
    VideoScriptAgentPanel.tsx
    VideoBreakdownResultPanel.tsx
    AgentRunStatus.tsx
    ConversationPanel.tsx
  hooks/
    useAgentRunPolling.ts
  lib/
    api.ts
    perf.ts
docs/
  API.md
  PRD.md
  TODO.md
  STORAGE_SQLITE.md
  CODEX_HANDOFF.md
  NEXT_TASKS.md
  CHANGELOG_CONTEXT.md
AGENTS.md
```

## 已完成版本记录

### v1.5.7：文档乱码修复与 SQLite 存储底座迁移

- 修复并重写 `docs/API.md`、`docs/PRD.md` 为 UTF-8。
- 新增 APP SQLite 初始化、迁移和 health。
- 新增 JSON 到 SQLite 幂等迁移。
- users、audit_logs、QA conversation、Agent conversation、agent_runs、connectors、debug_payloads、files、artifacts 迁入 APP SQLite。
- RAG SQLite 保持独立，只保存 documents/chunks/embedding。

### v1.5.8：存储性能优化与 Dataset SQLite 统一

- QA conversation 常规写入改为增量 upsert/update/insert。
- Agent conversation 常规写入改为增量 upsert/update/insert。
- bulk replace 仅保留给 legacy migration。
- Dataset metadata 从 `datasets.json` 迁入 APP SQLite。
- 新增 `datasets`、`dataset_files`、`dataset_jobs`。
- Dataset 文件本体仍在磁盘，不进入 SQLite。
- 新增 `service_events`，解除 `task_store` 与 `conversation_store` 的函数内延迟 import。

### v1.6：视频拆解智能体生产化

- 新增 `GET /api/agents/video-script/status`。
- 前端新增视频拆解连接状态、提交前预检、高级参数和失败提示。
- 视频拆解 workflow 标准化 steps。
- 结构化 result_json：summary、timeline、subtitles、selling_points、proof_frames、quality_warnings、files。
- 输出文件登记到 artifacts，支持安全下载。
- Debug Payload 保存 request/response/error。
- 8001 未启动时任务真实 failed，不伪造成功。

### v1.6.1：AI 智能体会话切换卡死修复

- `/agent?conversation_id=` 切换增加 AbortController。
- 过期请求通过 request sequence 忽略。
- 点击当前会话不重复请求。
- URL 同步使用 `window.history.replaceState`，避免 App Router 同路由 query 重载。
- 轮询清理补强。
- 大 JSON 文本截断，避免默认撑爆页面。

### v1.6.2：AI 智能体页面卡顿深度优化

- 后端新增 `GET /api/agent-runs/{run_id}/summary`。
- 后端新增 `GET /api/agent-runs/{run_id}/result`。
- conversation detail 默认返回轻量摘要，大 result/debug payload 不默认返回。
- 前端新增 `markPerf` 开发性能探针。
- 前端新增 `useAgentRunPolling`，统一 active run 轮询。
- GenericAgentPanel、VideoScriptAgentPanel、AgentRunStatus 不再各自 setInterval。
- VideoBreakdownResultPanel 改为 memo + tabs + “加载更多”。
- Debug Payload 和完整 result 改为按需加载。
- 文档新增 `docs/AGENT_PERFORMANCE_NOTES.md`。

### v1.6.3：架构评估 P1-P3 优化与工程规范补齐

- 前端新增 SWR/query hooks 基础层，低风险接入 `/agent`、`/chat` 会话列表和后台/知识库读取场景。
- DeepSeek 非流式问答新增 `async_generate_answer` / `async_ask`，保留同步兼容与稳定 SSE。
- 新增 `apps/api/scripts/smoke_minimal.py` 和 `docs/SMOKE_TESTS.md`。
- 根目录、API、Web 历史日志归档到 `apps/api/runtime/logs/archive/`。
- `docs/*.bak-v1.5.7` 移到 `docs/archive/legacy_bak_v1.5.7/`。
- 新增 `security_config_service.py`，支持缺失 secret 时生成 `generated_secrets.json`，runtime health 输出安全 warning。
- 补齐 Docker Compose、Dockerfile 和 GitHub Actions CI。

## 当前正在处理的问题

本轮只处理“新窗口交接包”落盘，不继续写新功能。当前用户重新指定的 P0 是回归 `/agent` 任务和聊天持久化链路：

1. 在 `/agent` 智能体界面执行任务后，左侧聊天记录必须新增并持久保存。
2. 切换到其他路由再回来，任务/聊天不能消失。
3. 脚本拆解智能体必须在提交任务后真实执行，而不是只创建 UI 状态。
4. 任务状态、结果、错误信息要能回显到对应聊天记录。

注意：v1.6.2 已做性能优化，但下一窗口仍应按 P0 做真实回归，不要只相信 UI。

## 最近一次用户明确要求

用户要求生成一个新窗口可继续接手的上下文交接包，只做总结和落盘，更新：

- `docs/CODEX_HANDOFF.md`
- `docs/NEXT_TASKS.md`
- `docs/CHANGELOG_CONTEXT.md`
- `AGENTS.md`

并输出文件摘要和可复制的新窗口启动提示词。

## 已经改过的关键文件

后端：

- `apps/api/main.py`
- `apps/api/routers/admin_runtime.py`
- `apps/api/routers/agent_runs.py`
- `apps/api/routers/agents.py`
- `apps/api/routers/artifacts.py`
- `apps/api/routers/conversations.py`
- `apps/api/routers/datasets.py`
- `apps/api/routers/qa_chat.py`
- `apps/api/routers/qa_knowledge.py`
- `apps/api/services/app_sqlite.py`
- `apps/api/services/app_sqlite_migrations.py`
- `apps/api/services/json_to_sqlite_migrator.py`
- `apps/api/services/task_store.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/qa_conversation_store.py`
- `apps/api/services/dataset_store.py`
- `apps/api/services/service_events.py`
- `apps/api/services/video_agent_status_service.py`
- `apps/api/workflows/video_script_workflow.py`

前端：

- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/app/chat/page.tsx`
- `apps/web/src/lib/api.ts`
- `apps/web/src/lib/perf.ts`
- `apps/web/src/hooks/useAgentRunPolling.ts`
- `apps/web/src/components/GenericAgentPanel.tsx`
- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/web/src/components/AgentRunStatus.tsx`
- `apps/web/src/components/ConversationPanel.tsx`
- `apps/web/src/components/VideoBreakdownResultPanel.tsx`
- `apps/web/src/components/RuntimeHealthPanel.tsx`
- `apps/web/src/components/KnowledgeBasePanel.tsx`
- `apps/web/src/components/DatasetPanel.tsx`
- `apps/web/src/components/AdminConsolePanel.tsx`

文档/配置：

- `.gitignore`
- `.env.example`
- `AGENTS.md`
- `docs/API.md`
- `docs/PRD.md`
- `docs/TODO.md`
- `docs/STORAGE_SQLITE.md`
- `docs/VIDEO_AGENT_SETUP.md`
- `docs/AGENT_PERFORMANCE_NOTES.md`
- `docs/CODEX_HANDOFF.md`
- `docs/NEXT_TASKS.md`
- `docs/CHANGELOG_CONTEXT.md`

## 数据库/API/前端状态

- `/health` 保持 `{"status":"ok","service":"meizhaiseek-api"}`。
- `/api/admin/runtime/health` 当前应返回 `version = v1.6.3`。
- `/api/admin/storage/health` 返回 APP SQLite 表统计和 legacy JSON 状态。
- `GET /api/agent-runs/{run_id}/summary` 用于轻量轮询。
- `GET /api/agent-runs/{run_id}/result` 用于按需读取完整 result。
- `GET /api/conversations/{conversation_id}` 保持 wire shape，但大字段返回 preview/summary。
- `/chat` 流式问答不应被后续改动影响。
- `/agent` 页面轮询统一在 `useAgentRunPolling.ts`，子组件不应再创建自己的 interval。
- Dataset metadata 主存储是 APP SQLite；文件本体仍在磁盘。
- Debug Payload 详情不在会话切换时默认加载。

## 已知 bug / 风险

- 用户仍要求优先回归 `/agent` 执行任务后左侧会话持久化、路由恢复和状态回写，说明真实使用中这条链路仍需重点验证。
- 8001 local agent 是外部服务。未启动时 failed 是正确行为；不要为了验收伪造成 completed。
- `NEXT_PUBLIC_API_BASE_URL` 在前端 build 时固化，构建前必须设为 `http://localhost:8000`。
- runtime、SQLite、uploads、models、logs 都被 `.gitignore` 排除，GitHub 不包含本地运行数据。
- 文档备份文件 `docs/API.md.bak-v1.5.7`、`docs/PRD.md.bak-v1.5.7` 可能保留历史乱码，仅用于追溯。

## 不能破坏的功能

- v1.2 登录鉴权、`auth_version`、用户隔离、admin/operator/viewer 权限。
- v1.3 Connector、Payload Preview、Debug Payload、Replay。
- v1.4 管理员账号管理、审计日志、权限、SafeDrawer/滚动修复。
- v1.5 Dataset、字段映射、清洗、导出、安全下载。
- v1.5.2 QA 首屏问答和 QA conversation。
- v1.5.3 知识库上传、删除、重新索引、RAG sources。
- v1.5.4 二级会话栏收缩/展开、会话归档删除。
- v1.5.5 模型状态、Embedding 测试、RAG 检索测试、知识库诊断。
- v1.5.6 QA 流式输出、停止生成、非流式 fallback。
- v1.5.7 APP SQLite 与 RAG SQLite 分离。
- v1.5.8 conversation 增量 upsert、Dataset SQLite、service_events。
- v1.6 视频拆解连接预检、真实执行、结构化结果、artifact 下载。
- v1.6.2 `/agent` 轻量 payload、单一轮询、延迟加载和分段渲染。

## 下一窗口必须优先读取的文件

1. `AGENTS.md`
2. `docs/CODEX_HANDOFF.md`
3. `docs/NEXT_TASKS.md`
4. `docs/CHANGELOG_CONTEXT.md`
5. `docs/API.md`
6. `docs/PRD.md`
7. `docs/STORAGE_SQLITE.md`
8. `docs/AGENT_PERFORMANCE_NOTES.md`
9. `apps/api/main.py`
10. `apps/api/routers/agent_runs.py`
11. `apps/api/routers/conversations.py`
12. `apps/api/services/task_store.py`
13. `apps/api/services/conversation_store.py`
14. `apps/api/services/service_events.py`
15. `apps/api/workflows/video_script_workflow.py`
16. `apps/web/src/app/agent/page.tsx`
17. `apps/web/src/lib/api.ts`
18. `apps/web/src/hooks/useAgentRunPolling.ts`
19. `apps/web/src/components/VideoScriptAgentPanel.tsx`
20. `apps/web/src/components/AgentRunStatus.tsx`

## 新窗口启动提示词

```text
请继续接手 E:\USE\codexhome\agents-cowork\meizhaiseek-platform。当前版本是 meizhaiseek v1.6.3，GitHub 仓库是 https://github.com/zhuge1hao/seek-platform.git，但请先读取磁盘代码和文档，不要只依赖历史对话或 Git 状态。

第一步完整读取 AGENTS.md、docs/CODEX_HANDOFF.md、docs/NEXT_TASKS.md、docs/CHANGELOG_CONTEXT.md、docs/API.md、docs/PRD.md、docs/STORAGE_SQLITE.md、docs/AGENT_PERFORMANCE_NOTES.md，然后按 NEXT_TASKS 的 P0 做最小必要处理和验证。

当前最优先任务是回归 /agent：1）在 /agent 智能体界面执行任务后，左侧聊天记录必须新增并持久保存；2）切换到其他路由再回来，任务/聊天不能消失；3）脚本拆解智能体必须在提交任务后真实执行，而不是只创建 UI 状态；4）任务状态、结果、错误信息要能回显到对应聊天记录。

如果视频脚本任务报 local agent 8001 无法连接，不要伪造成成功。先确认 3000/8000 是否启动，再确认是否存在真实 local agent 服务并启动 POST http://localhost:8001/api/agent/run。若没有真实 local agent，只能报告外部服务缺失，平台按设计 failed。

不要破坏 v1.2 鉴权隔离、v1.3 Connector/Debug、v1.4 管理员/审计/权限/滚动、v1.5 Dataset、v1.5.2-v1.5.6 QA/RAG/流式问答、v1.5.7 APP SQLite 迁移、v1.5.8 增量 upsert/Dataset SQLite/service_events、v1.6 视频拆解生产化、v1.6.2 /agent 性能优化。修改后运行 python -m compileall apps/api 和 apps/web 下 NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build。
```
