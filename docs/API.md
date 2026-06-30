# meizhaiseek API 文档

本文档为 UTF-8 编码，记录 meizhaiseek v1.6.3 的主要后端接口。除 `/health` 和登录接口外，业务接口默认需要 `Authorization: Bearer <token>`。

## 基础健康

- `GET /health`：公开健康检查，返回 `{"status":"ok","service":"meizhaiseek-api"}`。
- `GET /api/admin/runtime/health`：管理员运行时健康检查，返回服务名、版本 `v1.6.3`、配置状态和 warnings。v1.6.3 起 warnings 会包含默认开发 secret、默认初始管理员密码、runtime 生成 secret 等安全配置提示。

## 认证与用户管理

- `POST /api/auth/login`：用户名密码登录，返回 token、过期时间和当前用户信息。
- `POST /api/auth/logout`：记录退出审计日志。
- `GET /api/auth/me`：校验 token、用户启用状态和 `auth_version`。
- `POST /api/auth/change-password`：当前用户修改密码，成功后递增 `auth_version`。
- `GET /api/admin/users`：管理员查询用户。
- `POST /api/admin/users`：管理员创建 admin/operator/viewer 用户。
- `GET /api/admin/users/{user_id}`：管理员读取单个用户。
- `POST /api/admin/users/{user_id}`：管理员更新角色、启用状态和备注。
- `POST /api/admin/users/{user_id}/enable`：启用用户。
- `POST /api/admin/users/{user_id}/disable`：禁用用户；禁止禁用当前管理员或最后一个启用 admin。
- `POST /api/admin/users/{user_id}/reset-password`：重置密码并递增 `auth_version`。
- `GET /api/admin/users/{user_id}/agent-runs`：查看指定用户任务。
- `GET /api/admin/agent-runs`：管理员跨用户查询任务。

## 智能体配置与技能模板

- `GET /api/agents`：返回前端 22 个智能体注册信息。
- `GET /api/agent-configs`：返回前端智能体配置。
- `GET /api/agent-configs/{agent_type}`：返回单个智能体配置。
- `POST /api/agent-configs/{agent_type}`：部分更新智能体配置。
- `GET /api/skills`：返回技能列表。
- `GET /api/skills/templates`：按可选 `agent_type` 返回技能模板。
- `GET /api/skills/templates/{skill_id}`：返回单个技能模板。
- `POST /api/skills/templates`：新增或更新技能模板。
- `DELETE /api/skills/templates/{skill_id}`：软删除技能模板。

## 文件与 Artifact

- `POST /api/files/video/upload`：视频脚本拆解快捷上传，支持 `.mp4`、`.mov`、`.webm`、`.mkv`。
- `POST /api/files/upload`：通用文件上传，支持表格、文本、图片和常见视频格式。
- `GET /api/files?extensions=xlsx,xls,csv&limit=50`：列出当前用户上传文件。
- `GET /api/files/{file_id}/preview`：读取文件预览。
- `GET /api/artifacts/download?path=...`：下载安全目录内结果文件，按用户归属校验。

## AI 对话

- `GET /api/qa/health`：返回 QA 能力轻量健康状态，不返回 DeepSeek API Key。
- `GET /api/qa/conversations`：返回当前用户 AI 对话二级栏记录。
- `GET /api/qa/conversations/{conversation_id}`：返回当前用户单条 AI 对话和 messages。
- `POST /api/qa/conversations`：创建空 QA 对话。
- `POST /api/qa/conversations/{conversation_id}/archive`：软归档当前用户 QA 对话。
- `POST /api/qa/chat`：非流式问答。请求包含 `conversation_id`、`question`、`use_rag`、`top_k`，返回 `answer`、`sources`、`warnings`、`conversation_id`、`message_id`、`model`。
- `POST /api/qa/chat/stream`：SSE 流式问答。事件包括 `start`、`retrieval_start`、`sources`、`delta`、`done`、`error`。非流式 `/api/qa/chat` 保留为 fallback。

`POST /api/qa/chat` 请求示例：

```json
{
  "conversation_id": null,
  "question": "怎么打爆款？",
  "use_rag": true,
  "top_k": 5
}
```

成功返回示例：

```json
{
  "conversation_id": "qa_conv_xxx",
  "message_id": "msg_xxx",
  "answer": "回答内容",
  "sources": [],
  "warnings": [],
  "model": "deepseek-v4-flash"
}
```

## AI 对话知识库

- `POST /api/qa/knowledge/upload`：admin/operator 上传 txt、md、docx 并入库。
- `GET /api/qa/knowledge/documents`：当前用户知识库文档列表。
- `GET /api/qa/knowledge/documents/{doc_id}`：文档详情和最多 10 条 chunk preview。
- `DELETE /api/qa/knowledge/documents/{doc_id}`：admin/operator 删除自己的文档及 chunks。
- `POST /api/qa/knowledge/documents/{doc_id}/reindex`：admin/operator 重新索引文档。
- `GET /api/qa/knowledge/stats`：当前用户知识库统计。

上传成功返回示例：

```json
{
  "doc_id": "doc_xxx",
  "title": "文档标题",
  "status": "ready",
  "chunk_count": 12,
  "message": "文档入库完成"
}
```

## RAG 与模型诊断

- `GET /api/qa/model-status?include_load_check=false`：查看 bge-small-zh 路径、SQLite RAG、DeepSeek 配置状态；admin/operator/viewer 可用，不返回 API Key。
- `POST /api/qa/test-embedding`：admin/operator 测试 embedding，返回维度和 preview。
- `POST /api/qa/test-retrieval`：admin/operator 测试当前用户 RAG 检索，不调用 DeepSeek。
- `POST /api/qa/diagnose`：admin/operator 返回综合诊断 summary 和 checks。

## AI 智能体会话与任务

- `GET /api/conversations`：当前用户 AI 智能体会话列表。
- `GET /api/conversations/{conversation_id}`：会话详情、latest run 和 runs。
- `POST /api/conversations`：创建智能体会话。
- `POST /api/conversations/{conversation_id}/rename`：重命名会话。
- `POST /api/conversations/{conversation_id}/archive`：软归档会话。
- `POST /api/agent-runs`：提交智能体任务，返回 `run_id`、`conversation_id`、`status`。
- `GET /api/agent-runs`：当前用户任务列表。
- `GET /api/agent-runs/{run_id}`：查询任务状态、进度、日志、结果和错误。
- `POST /api/agent-runs/{run_id}/cancel`：取消 running 任务。
- `POST /api/agent-runs/{run_id}/retry`：基于原 payload 创建重试任务。
- `POST /api/agent-runs/preview-payload`：按智能体配置预览最终 Payload，不创建任务。

`POST /api/agent-runs` 支持 `selected_skill_ids`、`link`、`file_ids`、`dataset_ids`、`image_paths`、`video_path`、`video_url`、`session_id` 和 `workflow_options`。

## Local Agent Connector 与 Debug Payload

- `GET /api/agent-connectors`：列出连接器。
- `GET /api/agent-connectors/{connector_id}`：读取连接器。
- `POST /api/agent-connectors`：创建连接器。
- `POST /api/agent-connectors/{connector_id}`：更新连接器。
- `DELETE /api/agent-connectors/{connector_id}`：软禁用连接器。
- `POST /api/agent-connectors/{connector_id}/test`：测试 mock、HTTP、CLI 连接。
- `POST /api/agent-connectors/{connector_id}/preview-payload`：按连接器预览 Payload。
- `GET /api/admin/debug-payloads`：管理员查询联调记录。
- `GET /api/admin/debug-payloads/{run_id}`：读取 request、response、error。
- `POST /api/admin/debug-payloads/{run_id}/replay`：重放保存的 request。

## Dataset 数据清洗

- `POST /api/datasets/from-file`：基于当前用户的 `file_id` 创建 Dataset。
- `GET /api/datasets`：查询当前用户 Dataset；admin 可按参数查看全部或指定用户。
- `GET /api/datasets/mapping-templates`：读取当前用户可复用字段映射模板。
- `GET /api/datasets/{dataset_id}`：读取 Dataset 元数据。
- `GET /api/datasets/{dataset_id}/preview`：读取预览行和字段识别结果。
- `POST /api/datasets/{dataset_id}/field-mapping`：保存字段映射。
- `GET /api/datasets/{dataset_id}/field-mapping`：读取字段映射。
- `POST /api/datasets/{dataset_id}/clean`：执行同步清洗并生成 Excel、profile 和 metrics 文件。
- `GET /api/datasets/{dataset_id}/profile`：读取清洗画像。
- `GET /api/datasets/{dataset_id}/files`：读取结果文件。
- `DELETE /api/datasets/{dataset_id}`：软删除 Dataset。

## 后台运维

- `GET /api/admin/runtime/configs/status`：检查 agent_configs、skill_templates、files。
- `POST /api/admin/runtime/configs/backup`：备份 runtime configs。
- `POST /api/admin/runtime/configs/repair`：修复 runtime configs。
- `POST /api/admin/runtime/configs/reset`：重置默认配置。
- `GET /api/admin/runtime/configs/export`：导出配置。
- `POST /api/admin/runtime/cache/clear`：清理可清理缓存。
- `GET /api/admin/agent-runs/stats`：任务统计。
- `POST /api/admin/agent-runs/repair-stale`：修复超时 running 任务。
- `POST /api/admin/agent-runs/cleanup`：清理历史任务。
- `GET /api/admin/audit-logs`：查询审计日志。
- `GET /api/admin/audit-logs/export`：导出审计日志 CSV 或 JSONL。

## v1.5.7 APP SQLite 存储

- `GET /api/admin/storage/health`：仅 admin，返回 APP SQLite 路径、表计数、JSON 迁移状态。
- `POST /api/admin/storage/migrate-json`：仅 admin，手动触发旧 JSON 备份和幂等迁移。

APP SQLite 默认路径为 `apps/api/runtime/app/meizhaiseek.sqlite3`。RAG SQLite 仍为 `apps/api/runtime/rag/rag.sqlite3`，两者独立管理。

## v1.5.8 存储性能优化与 Dataset SQLite 统一

- v1.5.8 没有新增业务接口，主要是底层存储与性能优化，现有 API 返回结构保持兼容。
- Dataset API 底层 metadata 已迁入 APP SQLite；Excel、图片、清洗结果等文件本体仍保存在磁盘。
- `GET /api/admin/storage/health` 的 `tables` 返回新增 `datasets`、`dataset_files`、`dataset_jobs` 统计；`legacy_json` 返回新增 Dataset migration 状态和 warnings。
## v1.6 视频拆解智能体生产化

- `GET /api/agents/video-script/status`：登录用户可查看本地视频拆解 Agent 连接状态。返回 `connected/disconnected/mock/disabled`、`base_url`、`reachable`、`latency_ms`、中文提示和启动建议；本地 8001 不可达时不返回 500。
- `POST /api/agent-runs`：`agent_type=video_script_breakdown` 时支持 `mode`、`video_path`、`video_url`、`session_id` 和 `workflow_options`。推荐 mode 为 `standard_breakdown`、`no_subtitle_breakdown`、`fast_breakdown`、`quality_check`。
- `workflow_options_json`：保存 OCR、音频转写、Excel/JSON/keyframes 输出、质量检查、Debug Payload、输出目录和固定 session_id 等视频拆解参数。
- `result_json`：视频拆解结果包含 `summary`、`timeline`、`subtitles`、`selling_points`、`proof_frames`、`quality_warnings`、`files`、`steps`；缺失字段以空数组或 null 兼容。
- Artifact 下载：保留 `/api/artifacts/download?path=...`，并新增 run-scoped 下载 `/api/agent-runs/{run_id}/artifacts/{artifact_id}/download`，下载前校验用户、run、artifact 归属和安全路径。
## v1.6.2 Performance

v1.6.2 新增 `GET /api/agent-runs/{run_id}/summary` 和 `GET /api/agent-runs/{run_id}/result`。`summary` 用于 `/agent` 页面轻量轮询，返回任务状态、进度、步骤摘要、artifact 计数和 result preview；`result` 用于用户展开完整结果时按需读取完整 `result_json`。`GET /api/conversations/{conversation_id}` 保持原 wire shape，但其中 run/message 大字段默认返回 preview，Debug Payload 仍走后台详情接口。

## v1.6.3 Engineering

v1.6.3 无新增业务 API。`GET /api/admin/runtime/health` 的 `version` 返回 `v1.6.3`，`warnings` 增加安全配置提示。新增本地 smoke 脚本 `python apps/api/scripts/smoke_minimal.py`，用于验证 `/health`、登录、conversation、agent run、SQLite 持久化、storage health 和 QA model status。

## v1.6.1 Hotfix

v1.6.1 无新增业务接口，主要修复 `/agent` 会话切换稳定性。现有 Agent、视频拆解、Artifact、Debug Payload、Dataset、RAG 和 `/chat` 接口保持兼容。
