# Changelog Context

本文件记录跨 Codex 窗口的变更上下文，不替代正式 release notes。当前仓库已初始化 Git，并已推送到 `https://github.com/zhuge1hao/seek-platform.git`。继续接手仍应先读磁盘文件和本文件，不要只依赖历史对话。

## 当前状态摘要

- 当前版本：`meizhaiseek v1.6.3`
- `/health`：`{"status":"ok","service":"meizhaiseek-api"}`
- `/api/admin/runtime/health`：应返回 `version = v1.6.3`
- APP SQLite：`apps/api/runtime/app/meizhaiseek.sqlite3`
- RAG SQLite：`apps/api/runtime/rag/rag.sqlite3`
- GitHub：`https://github.com/zhuge1hao/seek-platform.git`
- 最近提交：本轮提交 `chore: optimize architecture P1-P3 items`
- 运行数据、模型、上传文件、日志均被 `.gitignore` 排除，不在 GitHub。

## 版本脉络

### v1.5.2：AI 对话首屏问答功能

- 新增真实 `/chat` 问答链路。
- 后端使用 FastAPI QA API。
- 本地 `bge-small-zh` 负责中文向量化。
- RAG SQLite 存储 documents/chunks/embedding。
- DeepSeek 非流式回答。
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

- DeepSeek client 新增 streaming。
- 新增 `qa_stream_service.py`。
- 新增 `POST /api/qa/chat/stream`。
- 前端用 `fetch + ReadableStream` 解析 SSE。
- 支持停止生成、复制回答、重新生成。
- 完成/失败/停止都持久化 assistant message。
- 非流式 `/api/qa/chat` 保留 fallback。

### v1.5.7：文档乱码修复与 SQLite 存储底座迁移

- 修复 `docs/API.md`、`docs/PRD.md` 乱码。
- 新增 `docs/STORAGE_SQLITE.md`。
- 新增 APP SQLite 初始化和 migrations。
- 新增 JSON 到 SQLite 幂等迁移。
- 新增 `GET /api/admin/storage/health`。
- 新增 `POST /api/admin/storage/migrate-json`。
- 主写入 store 切换到 APP SQLite：
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

### v1.5.8：存储性能优化与 Dataset SQLite 统一

- `qa_conversation_store.py` 常规写入取消 DELETE + 全量 INSERT。
- `conversation_store.py` 常规写入取消 DELETE + 全量 INSERT。
- bulk replace 函数只保留给 legacy migration。
- Dataset metadata 迁入 APP SQLite。
- 新增 `datasets`、`dataset_files`、`dataset_jobs`。
- `datasets.json` 只作为迁移源和 fallback read。
- Dataset 文件本体继续保存在磁盘。
- 新增 `service_events.py`。
- `task_store.py` 通过 run updated event 同步 conversation，不再函数内 import `conversation_store`。

### v1.6：视频拆解智能体生产化

- 视频拆解成为第一个正式业务智能体样板。
- 新增 `GET /api/agents/video-script/status`。
- 后端检测 `video_script_agent` local connector，前端不直连 8001。
- 前端新增连接状态卡片、测试连接、提交前预检。
- 支持拆解模式和高级参数写入 `workflow_options_json`。
- `video_script_workflow` 标准化 steps。
- `result_json` 归一化为 summary、timeline、subtitles、selling_points、proof_frames、quality_warnings、files。
- 输出文件登记 artifacts。
- Artifact 下载做用户所有权和安全路径校验。
- Debug Payload 保存 request/response/error。
- 8001 不可达时 run 真实 failed。

### v1.6.1：AI 智能体会话切换稳定性修复

- `/agent?conversation_id=` detail 请求支持 AbortController。
- requestSeq 忽略过期响应。
- 点击当前会话直接 return。
- URL 同步使用原生 `window.history.replaceState`。
- 切换会话时清理旧 polling。
- 大 JSON 文本默认截断。
- 删除按钮阻止事件冒泡。
- conversation 不存在时清理 URL 和 localStorage。

### v1.6.2：AI 智能体页面卡顿深度优化

- 后端 payload 轻量化。
- 新增 `GET /api/agent-runs/{run_id}/summary`。
- 新增 `GET /api/agent-runs/{run_id}/result`。
- `/api/conversations/{conversation_id}` 默认返回 conversation + message 摘要 + run summary。
- 新增 `apps/web/src/lib/perf.ts`，开发环境耗时探针。
- 新增 `apps/web/src/hooks/useAgentRunPolling.ts`，统一 `/agent` active run 轮询。
- 子组件移除重复 setInterval。
- `VideoBreakdownResultPanel` 改为 memo + tabs + load more。
- Debug Payload 不在会话切换时默认加载。
- Artifact 内容不在切换会话时批量加载。
- 新增 `docs/AGENT_PERFORMANCE_NOTES.md`。
- 已推送 GitHub 首个 commit：`dc88a86`。

### v1.6.3：架构评估 P1-P3 优化与工程规范补齐

- 引入 SWR 基础数据获取层和读取型 hooks。
- `/agent`、`/chat` 会话列表及后台/知识库低风险读取场景接入 SWR。
- DeepSeek 非流式问答新增 async wrapper，保留同步和 SSE 流式兼容。
- 新增最小 smoke 脚本与 `docs/SMOKE_TESTS.md`。
- 根目录和前端/API 散落日志归档到 `apps/api/runtime/logs/archive/`。
- `docs/*.bak-v1.5.7` 归档到 `docs/archive/legacy_bak_v1.5.7/`。
- 新增 runtime secret 生成式初始化和 runtime health 安全 warning。
- 补齐 Docker Compose、Dockerfile 和 GitHub Actions 最小 CI。

## 最近验证记录

最近一轮 v1.6.3 开发已通过：

- `python -m compileall apps/api`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build`
- `/health` 返回 `meizhaiseek-api`
- `/api/admin/runtime/health` 返回 `v1.6.3`
- summary/result endpoints 基础 smoke
- 禁止词扫描在 `apps docs` 范围无命中
- 导航仍显示“美宅BI”“万能美虾”

本轮交接包只改文档，未重跑构建。

## 当前风险

- 用户再次明确 P0 是 `/agent` 任务执行后的会话持久化、路由恢复、真实执行和状态回写，需要下一窗口优先真实验证。
- 8001 local agent 不属于平台内置服务，未启动时 failed 是正确行为。
- GitHub 不包含 runtime 数据；新机器拉仓库后需要按 `.env.example` 和文档准备运行环境。
- `docs/API.md.bak-v1.5.7`、`docs/PRD.md.bak-v1.5.7` 可能保留历史乱码，正式阅读以当前 docs 为准。

## 后续最重要检查点

1. `/agent` 新任务是否写入 `agent_conversations`、`agent_messages`、`agent_runs`。
2. `/agent` 切路由/刷新后是否恢复 conversation 和 latest run。
3. 视频脚本任务是否真实进入后端 orchestrator/workflow。
4. local agent 8001 不可达时是否真实 failed 并回写 assistant message。
5. run updated event handler 是否仍生效。
6. `/agent` 是否仍只有单一 summary polling。
7. storage health 是否持续返回 SQLite 表计数。
