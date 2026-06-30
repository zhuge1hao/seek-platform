# Codex Handoff

## 项目名称与当前版本

- 项目：`meizhaiseek-platform`
- 当前版本：`meizhaiseek v1.6`
- 工作目录：`E:\USE\codexhome\agents-cowork\meizhaiseek-platform`
- 日期：2026-06-29
- Git 状态：该目录没有 `.git` 元数据，不能依赖 `git diff` / `git status`。本交接基于当前磁盘文件、运行验证记录和用户上下文整理。

## 当前项目目标

meizhaiseek 是面向电商经营全链路的 AI 平台。当前主目标是保持 `/chat` AI 对话、RAG 知识库、流式输出、模型诊断、`/agent` 智能体任务、Connector、Debug Payload、Dataset、后台账号和审计能力稳定，并在 v1.5.7 之后继续排查 `/agent` 会话持久化和真实任务执行链路。

## 技术栈与启动方式

- 前端：Next.js 14 App Router、React 18、TypeScript、Tailwind CSS、lucide-react。
- 后端：FastAPI、Uvicorn、Pydantic、requests、标准库 `sqlite3`。
- AI 问答：DeepSeek OpenAI-compatible Chat Completions，非流式和 SSE 流式均保留。
- Embedding：本地 `bge-small-zh`，通过 `sentence-transformers` 懒加载。
- 存储：
  - APP SQLite：`apps/api/runtime/app/meizhaiseek.sqlite3`，保存平台运行数据。
  - RAG SQLite：`apps/api/runtime/rag/rag.sqlite3`，保存知识库 documents/chunks/embedding。
  - legacy JSON：仅作为迁移来源、备份和兜底排查，不再作为主写入目标。

启动：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

分开启动：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\api
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run dev -- -p 3000
```

构建验证：

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
  schemas/
  services/
    app_sqlite.py
    app_sqlite_migrations.py
    json_to_sqlite_migrator.py
    qa_* service files
    conversation_store.py
    task_store.py
  workflows/
  runtime/
    app/meizhaiseek.sqlite3
    rag/rag.sqlite3
    legacy_json_backups/
    users/{user_id}/
apps/web/src/
  app/
    chat/
    agent/
  components/
  lib/api.ts
docs/
  API.md
  PRD.md
  TODO.md
  STORAGE_SQLITE.md
  RAG_MODEL_SETUP.md
  CODEX_HANDOFF.md
  NEXT_TASKS.md
  CHANGELOG_CONTEXT.md
AGENTS.md
```

## 已完成版本记录

### v1.5.6：AI 对话流式输出与回答体验优化

- 新增 `POST /api/qa/chat/stream`。
- DeepSeek client 支持 `stream=true`。
- 前端 `/chat` 使用 `fetch + ReadableStream` 解析 SSE。
- 支持 `start`、`retrieval_start`、`sources`、`delta`、`done`、`error`。
- 支持停止生成、复制回答、重新生成、sources 折叠展示。
- 流式完成/失败/停止后写回 QA conversation。
- 非流式 `/api/qa/chat` 保留为 fallback。

### v1.5.7：文档乱码修复与 SQLite 存储底座迁移

- 修复并重写 `docs/API.md`、`docs/PRD.md` 为 UTF-8。
- 备份原文件：`docs/API.md.bak-v1.5.7`、`docs/PRD.md.bak-v1.5.7`。
- 新增 APP SQLite：
  - `apps/api/services/app_sqlite.py`
  - `apps/api/services/app_sqlite_migrations.py`
  - `apps/api/services/json_to_sqlite_migrator.py`
- 新增表：users、audit_logs、qa_conversations、qa_messages、agent_conversations、agent_messages、agent_runs、local_agent_connectors、debug_payloads、files、artifacts、app_kv、schema_migrations。
- 旧 JSON 启动时自动备份并幂等迁移到 SQLite。
- 新增后台接口：
  - `GET /api/admin/storage/health`
  - `POST /api/admin/storage/migrate-json`
- 核心 store 已切 SQLite 主读写：用户、审计、QA 会话、Agent 会话、Agent runs、Connector、Debug Payload、files metadata。
- RAG SQLite 保持独立，不迁移、不合并。
- `docs/STORAGE_SQLITE.md` 新增。

## 当前正在处理的问题

最近用户要求生成新窗口接手包。本轮只做总结和落盘，不继续写新功能。

下一窗口仍需优先处理 `/agent` 任务链路的 P0 回归：

1. 在 `/agent` 智能体界面执行任务后，左侧聊天记录必须新增并持久保存。
2. 切换到其他路由再回来，任务/聊天不能消失。
3. 脚本拆解智能体必须在提交任务后真实执行，而不是只创建 UI 状态。
4. 任务状态、结果、错误信息要能回显到对应聊天记录。

注意：如果真实 local agent 8001 服务不存在，视频脚本任务失败是正确行为，不能伪造成成功。

## 最近一次用户明确要求

用户要求创建新窗口可继续接手的上下文交接包，落盘：

- `docs/CODEX_HANDOFF.md`
- `docs/NEXT_TASKS.md`
- `docs/CHANGELOG_CONTEXT.md`
- `AGENTS.md`

并输出创建/修改文件摘要和可复制的新窗口启动提示词。

## 已经改过的关键文件

后端：

- `apps/api/main.py`
- `apps/api/routers/admin_runtime.py`
- `apps/api/routers/qa_chat.py`
- `apps/api/routers/qa_knowledge.py`
- `apps/api/services/app_sqlite.py`
- `apps/api/services/app_sqlite_migrations.py`
- `apps/api/services/json_to_sqlite_migrator.py`
- `apps/api/services/user_store.py`
- `apps/api/services/audit_log_service.py`
- `apps/api/services/qa_conversation_store.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`
- `apps/api/services/agent_connector_store.py`
- `apps/api/services/debug_payload_service.py`
- `apps/api/services/file_store.py`
- `apps/api/services/deepseek_client.py`
- `apps/api/services/qa_stream_service.py`
- `apps/api/services/qa_model_diagnostic_service.py`
- `apps/api/services/qa_rag_store.py`
- `apps/api/services/qa_rag_retriever.py`
- `apps/api/services/qa_document_ingest_service.py`

前端：

- `apps/web/src/app/chat/page.tsx`
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/lib/api.ts`
- `apps/web/src/components/ConversationPanel.tsx`
- `apps/web/src/components/KnowledgeBasePanel.tsx`
- `apps/web/src/components/AdminConsolePanel.tsx`
- `apps/web/src/components/RuntimeHealthPanel.tsx`
- `apps/web/src/components/DatasetPanel.tsx`
- `apps/web/src/components/AgentConfigPanel.tsx`

文档与配置：

- `.env.example`
- `AGENTS.md`
- `docs/API.md`
- `docs/PRD.md`
- `docs/TODO.md`
- `docs/STORAGE_SQLITE.md`
- `docs/RAG_MODEL_SETUP.md`
- `docs/CODEX_HANDOFF.md`
- `docs/NEXT_TASKS.md`
- `docs/CHANGELOG_CONTEXT.md`

## 数据库/API/前端状态

- `/health`：保持 `{"status":"ok","service":"meizhaiseek-api"}`。
- `/api/admin/runtime/health`：返回 `version = v1.6`。
- `/api/admin/storage/health`：admin 可访问，返回 APP SQLite 表计数和 JSON 迁移状态。
- APP SQLite 已存在：`apps/api/runtime/app/meizhaiseek.sqlite3`。
- RAG SQLite 已存在并独立保留：`apps/api/runtime/rag/rag.sqlite3`。
- legacy JSON backup 已存在：`apps/api/runtime/legacy_json_backups/...`。
- `/chat`：
  - QA 会话、知识库、RAG 诊断、流式问答均已接入。
  - DeepSeek API Key 只从后端环境变量读取。
- `/agent`：
  - 已有智能体会话栏、任务提交、状态轮询、取消、重试、archive。
  - 下一步需继续回归“提交后左侧记录新增并持久化、路由切换恢复、状态回写消息”。
- 前端构建最近已通过：`npm.cmd run build`。
- 后端编译最近已通过：`python -m compileall apps/api`。

## 已知 bug / 风险

- 目录无 `.git`，无法生成可信 git diff。
- 文档备份文件可能保留历史乱码，这是备份用途；正式 `API.md` / `PRD.md` 已修复为 UTF-8。
- local agent 8001 不属于当前平台内置服务；如果未启动，视频脚本任务应真实 failed。
- `NEXT_PUBLIC_API_BASE_URL` 在 build 时固化，构建前必须设置为正确 API 地址。
- SQLite 迁移是幂等设计，但 store 替换涉及面大，下一次改动必须回归登录、权限、用户隔离、QA、Agent、Connector、Dataset。

## 不能破坏的功能

- v1.2 登录鉴权、`auth_version`、用户隔离、admin/operator/viewer 权限。
- v1.3 Connector、Payload Preview、Debug Payload、Replay。
- v1.4 管理员账号管理、审计日志、权限、SafeDrawer/滚动修复。
- v1.5 Dataset、字段映射、清洗、导出、安全下载。
- v1.5.2 QA 首屏问答和 QA conversation。
- v1.5.3 知识库上传、删除、重索引、RAG sources。
- v1.5.4 二级会话栏收缩/展开、会话归档删除。
- v1.5.5 模型状态、Embedding 测试、RAG 检索测试、知识库诊断。
- v1.5.6 QA 流式输出、停止生成、非流式 fallback。
- v1.5.7 APP SQLite 与 RAG SQLite 分离。

## 下一窗口必须优先读取的文件

1. `AGENTS.md`
2. `docs/CODEX_HANDOFF.md`
3. `docs/NEXT_TASKS.md`
4. `docs/CHANGELOG_CONTEXT.md`
5. `docs/API.md`
6. `docs/PRD.md`
7. `docs/STORAGE_SQLITE.md`
8. `apps/api/main.py`
9. `apps/api/services/app_sqlite.py`
10. `apps/api/services/json_to_sqlite_migrator.py`
11. `apps/api/services/conversation_store.py`
12. `apps/api/services/task_store.py`
13. `apps/api/routers/agent_runs.py`
14. `apps/api/routers/conversations.py`
15. `apps/web/src/app/agent/page.tsx`
16. `apps/web/src/lib/api.ts`

## 新窗口启动提示词

```text
请继续接手 E:\USE\codexhome\agents-cowork\meizhaiseek-platform。该目录没有 Git 元数据，不要假定工作树干净，不要依赖 git diff；必须直接读取磁盘代码和文档。

第一步完整读取 AGENTS.md、docs/CODEX_HANDOFF.md、docs/NEXT_TASKS.md、docs/CHANGELOG_CONTEXT.md、docs/API.md、docs/PRD.md、docs/STORAGE_SQLITE.md，然后按 NEXT_TASKS 的 P0 做最小必要处理/验证。

当前版本是 meizhaiseek v1.6。v1.5.8 是存储性能优化与 Dataset SQLite 统一；v1.6 是视频拆解智能体生产化。APP SQLite 位于 apps/api/runtime/app/meizhaiseek.sqlite3，RAG SQLite 位于 apps/api/runtime/rag/rag.sqlite3，二者不能合并。

当前最优先任务是回归 /agent：执行任务后左侧聊天记录必须新增并持久保存；切换路由再回来任务/聊天不能消失；脚本拆解智能体提交后必须真实执行后端任务而不是只创建 UI 状态；任务状态、结果、错误信息要回显到对应聊天记录。

如果视频脚本任务报 local agent 8001 无法连接，不要伪造成成功。先确认 3000/8000 是否启动，再确认是否存在真实 local agent 服务并启动 POST http://localhost:8001/api/agent/run。若没有真实 local agent，只能报告外部服务缺失，平台按设计 failed。

不要破坏 v1.2 鉴权隔离、v1.3 Connector/Debug、v1.4 管理员/审计/权限/滚动、v1.5 Dataset、v1.5.2-v1.5.6 QA/RAG/流式问答、v1.5.7 APP SQLite 迁移。修改后运行 python -m compileall apps/api 和 apps/web 下 NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build。
```
## v1.5.8 存储性能优化与 Dataset SQLite 统一
- 当前版本固定为 `meizhaiseek v1.6`，`/api/admin/runtime/health` 返回 `version = v1.6`。
- QA conversation 与 Agent conversation 常规写入改为增量 upsert/update/insert；bulk replace 仅保留给 legacy migration。
- Dataset metadata 已迁入 APP SQLite 的 `datasets`、`dataset_files`、`dataset_jobs`，文件本体仍保留在磁盘。
- `service_events` 负责 run updated 本地轻量事件，`task_store` 不再函数内延迟 import `conversation_store`。
- APP SQLite 与 RAG SQLite 边界不变；RAG SQLite 仍只保存 documents/chunks/embedding。

## v1.6 视频拆解智能体生产化
- 当前版本固定为 meizhaiseek v1.6，/api/admin/runtime/health 返回 version = v1.6。
- 视频拆解智能体新增本地 8001 状态检测、提交前预检、结构化步骤和结果面板。
- 输出文件写入 artifacts，Debug Payload 保留 request/response/error。
