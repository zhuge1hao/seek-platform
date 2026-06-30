# Changelog Context

本文件记录跨 Codex 窗口的变更上下文，不替代正式 release changelog。当前目录没有 `.git` 元数据，不能生成可信 `git diff`；以下内容来自磁盘文件、用户要求和已执行验证记录。

## 当前状态摘要

- 当前版本：`meizhaiseek v1.6`
- `/health`：保持 `{"status":"ok","service":"meizhaiseek-api"}`
- `/api/admin/runtime/health`：返回 `version = v1.6`
- APP SQLite：`apps/api/runtime/app/meizhaiseek.sqlite3`
- RAG SQLite：`apps/api/runtime/rag/rag.sqlite3`
- legacy JSON backup：`apps/api/runtime/legacy_json_backups/...`
- 正式文档：`docs/API.md`、`docs/PRD.md` 已修复为 UTF-8。
- 备份文档：`docs/API.md.bak-v1.5.7`、`docs/PRD.md.bak-v1.5.7` 保留。

## 版本脉络

### v1.5.2：AI 对话首屏问答功能

- 新增真实 `/chat` 问答链路。
- 后端使用 FastAPI QA API。
- bge-small-zh 负责中文向量化。
- SQLite RAG 存储 chunks。
- DeepSeek v4 Flash 非流式回答。
- QA 会话按用户持久化。

### v1.5.3：AI 对话知识库入库与 RAG 管理中心

- 新增 txt/md/docx 文档上传。
- 文本解析、清洗、chunk 切分。
- 使用 bge-small-zh 生成 embedding。
- 写入 RAG SQLite。
- 新增知识库列表、详情、删除、重新索引、stats。
- `/chat` sources 可展示入库文档来源。

### v1.5.4：会话栏交互优化版

- `/chat` 和 `/agent` 二级会话栏支持收缩/展开。
- QA conversation 支持 archive。
- Agent conversation 复用 archive。
- 删除二次确认。
- 收缩状态写入 localStorage。

### v1.5.5：本地模型状态与 RAG 可用性诊断

- 新增 `/api/qa/model-status`。
- 新增 `/api/qa/test-embedding`。
- 新增 `/api/qa/test-retrieval`。
- 新增 `/api/qa/diagnose`。
- KnowledgeBasePanel 展示模型、RAG、DeepSeek 状态。
- 新增 `docs/RAG_MODEL_SETUP.md`。

### v1.5.6：AI 对话流式输出与回答体验优化

- DeepSeek client 新增 `stream_answer`。
- 新增 `qa_stream_service.py`。
- 新增 `POST /api/qa/chat/stream`。
- 前端用 `fetch + ReadableStream` 解析 SSE。
- 支持停止生成、复制回答、重新生成。
- 完成/失败/停止都持久化 assistant message。
- 非流式 `/api/qa/chat` 保留。

### v1.5.7：文档乱码修复与 SQLite 存储底座迁移

- 修复 `docs/API.md`、`docs/PRD.md` 乱码。
- 新增 `docs/STORAGE_SQLITE.md`。
- 新增 APP SQLite 初始化和 migrations。
- 新增 JSON 到 SQLite 幂等迁移。
- 新增 `GET /api/admin/storage/health`。
- 新增 `POST /api/admin/storage/migrate-json`。
- 切换主写入 store：
  - users
  - audit_logs
  - qa_conversations / qa_messages
  - agent_conversations / agent_messages
  - agent_runs
  - local_agent_connectors
  - debug_payloads
  - files metadata
  - artifacts metadata
- RAG SQLite 保持独立。

## 最近验证记录

已通过：

- `python -m compileall apps/api`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build`
- `/health` 返回 `meizhaiseek-api`
- admin 登录成功
- `/api/admin/runtime/health` 返回 `v1.5.7`
- `/api/admin/storage/health` 返回 `status=ok`、`backend=sqlite`
- `/chat` 页面 HTTP 200
- 文档扫描未发现常见乱码标记
- `API_fixed.md` 中 75 个接口路径已补回 `API.md`

## 当前风险

- 没有 `.git`，无法得出完整真实 diff。
- APP SQLite store 替换涉及面较大，下一步需要继续回归登录、权限、用户隔离、Agent、QA、Connector、Dataset。
- 8001 local agent 不是当前项目内置服务；未启动时视频脚本任务 failed 是正确行为。
- 文档备份文件可能保留乱码，因为它们用于追溯，不代表正式文档。

## 关键数据结构

APP SQLite 表：

- `users`
- `audit_logs`
- `qa_conversations`
- `qa_messages`
- `agent_conversations`
- `agent_messages`
- `agent_runs`
- `local_agent_connectors`
- `debug_payloads`
- `files`
- `artifacts`
- `app_kv`
- `schema_migrations`

RAG SQLite 保持：

- `documents`
- `chunks`

## 后续最重要检查点

1. `/agent` 新任务是否写入 `agent_conversations`、`agent_messages`、`agent_runs`。
2. `/agent` 切路由/刷新后是否恢复会话和 latest run。
3. 视频脚本任务是否真实进入后端 Orchestrator/workflow。
4. local agent 8001 不可达时是否真实 failed 并回写 assistant message。
5. storage health 是否持续返回 SQLite 表计数。
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
