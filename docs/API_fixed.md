# meizhaiseek-platform API

当前后端服务名称为 `meizhaiseek-api`。前端只通过统一任务接口提交智能体任务，不直接调用具体子 agent。

## v1.2 鉴权说明

除 `/health` 和 `/api/auth/login` 外，主要 API 需要在请求头携带 `Authorization: Bearer <token>`。用户数据使用本地 JSON 保存，不使用数据库。

默认管理员：

```text
用户名：admin
密码：admin123
```

密码使用 PBKDF2-SHA256 保存，token 使用 HMAC-SHA256 签名。修改密码后旧 token 立即失效。

## POST /api/auth/login

使用用户名和密码登录，返回 token、过期时间与不含密码字段的用户信息。

## POST /api/auth/logout

记录退出审计日志。当前不维护 token 黑名单。

## GET /api/auth/me

验证 token、用户启用状态与 `auth_version`。

## POST /api/auth/change-password

校验原密码后修改密码，新密码至少 8 位；成功后必须重新登录。

## GET /api/admin/audit-logs

仅 admin 可用。支持 `action`、`user`、`status`、`start_time`、`end_time` 和 `limit` 筛选。

## GET /health

```json
{
  "status": "ok",
  "service": "meizhaiseek-api"
}
```

## GET /api/agents

返回前端 22 个智能体注册信息。

## GET /api/agent-configs

返回 22 个前端智能体配置。

## GET /api/agent-configs/{agent_type}

返回单个智能体配置。隐藏的 `competitor_analysis` 可通过单项接口访问。

## POST /api/agent-configs/{agent_type}

只更新传入字段，返回更新后的完整配置。`video_script_breakdown` 的 `session_id` 会自动回退为 `019dd824-f4bb-7273-8ac3-6e19b195ff82`。

## GET /api/skills

返回当前 mock 技能列表。

## GET /api/skills/templates

支持 query 参数 `agent_type`。传入后只返回 enabled 且适用于该智能体的技能模板。

## GET /api/skills/templates/{skill_id}

返回单个技能模板。

## POST /api/skills/templates

新增或更新技能模板，保存到本地 JSON。

## DELETE /api/skills/templates/{skill_id}

第一版为软删除，将 `enabled=false`。

## POST /api/files/video/upload

视频脚本拆解快捷上传接口，支持 `.mp4`、`.mov`、`.webm`、`.mkv`。

## POST /api/files/upload

通用文件上传接口，支持 `xlsx/xls/csv/txt/json/png/jpg/jpeg/webp/mp4/mov/webm/mkv`。

返回示例：

```json
{
  "file_id": "file_xxx",
  "filename": "demo.xlsx",
  "file_type": "excel",
  "saved_path": "apps/api/uploads/files/demo.xlsx",
  "size": 1200,
  "created_at": "2026-06-18 12:00:00",
  "preview_status": "pending",
  "message": "文件上传成功"
}
```

## GET /api/files/{file_id}/preview

文件预览接口。Excel/CSV 返回前 20 行，TXT/JSON 返回摘要，图片和视频返回安全下载信息。

## POST /api/agent-runs

创建统一 agent run。支持 `selected_skill_ids`、`link`、`file_ids`、`dataset_ids`、`image_paths` 和可选 `conversation_id`。新任务没有 conversation_id 时自动创建会话；返回同时包含 `run_id` 和 `conversation_id`。

```json
{
  "agent_type": "smart_selection",
  "mode": "default",
  "prompt": "用户原始提示词",
  "selected_skill_ids": ["smart_selection_basic"],
  "link": "",
  "file_ids": ["file_xxx"],
  "image_paths": [],
  "video_path": "",
  "video_url": "",
  "session_id": "",
  "workflow_options": {}
}
```

## v1.5.1 Conversation

- `GET /api/conversations?limit=50&include_archived=false`：返回当前登录用户的真实会话列表。
- `GET /api/conversations/{conversation_id}`：返回 `{conversation, latest_run, runs, warnings}`；run 文件缺失时通过 warnings 提示。
- `POST /api/conversations/{conversation_id}/rename`：请求 `{ "title": "新标题" }`，仅可修改自己的会话。
- `POST /api/conversations/{conversation_id}/archive`：软归档自己的会话，不删除 run、消息或 artifact。

Conversation 保存于 `runtime/users/{user_id}/conversations/conversations.json`。任务状态、结果、错误、取消和重试均同步到对应 assistant message。

## v1.5.2 QA Chat

AI 对话接口均要求登录，admin、operator、viewer 都可使用。会话按当前 `user_id` 保存到 `runtime/users/{user_id}/qa_conversations/qa_conversations.json`，不复用智能体任务 conversation。

- `GET /api/qa/health`：返回 QA 能力状态，不返回 DeepSeek API Key。
- `GET /api/qa/conversations?limit=50`：返回当前用户 AI 对话二级栏记录。
- `GET /api/qa/conversations/{conversation_id}`：返回单条 AI 对话详情和 messages。
- `POST /api/qa/conversations`：创建空 AI 对话，请求 `{ "title": "新对话" }`。
- `POST /api/qa/chat`：提交问题，自动写入 user/assistant message。

`POST /api/qa/chat` 请求：

```json
{
  "conversation_id": null,
  "question": "怎么打爆款？",
  "use_rag": true,
  "top_k": 5
}
```

成功返回：

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

当 RAG 数据库为空时，接口允许 DeepSeek 直接回答并返回 warnings。当 `DEEPSEEK_API_KEY` 未配置时，接口返回中文错误，并在对应 conversation 中保留 failed assistant message。

## v1.5.3 QA Knowledge

AI 对话知识库接口均要求登录。admin、operator 可以上传、删除和重新索引自己的知识库文档；viewer 可以查看自己的文档、详情和统计，但不能管理。知识库文档写入 SQLite `documents`、`chunks` 表，按 `user_id` 隔离；DeepSeek API Key 不进入前端、日志或审计详情。

- `POST /api/qa/knowledge/upload`：上传并同步入库 `.txt`、`.md`、`.docx` 文档，multipart 字段为 `file` 和可选 `title`。
- `GET /api/qa/knowledge/documents`：返回当前用户知识库文档列表。
- `GET /api/qa/knowledge/documents/{doc_id}`：返回当前用户单个文档详情和最大 10 条 chunk preview。
- `DELETE /api/qa/knowledge/documents/{doc_id}`：软删除当前用户文档并删除对应 chunks。
- `POST /api/qa/knowledge/documents/{doc_id}/reindex`：重新解析源文件并重建 chunks。
- `GET /api/qa/knowledge/stats`：返回当前用户文档数、chunk 数、ready/failed 数量和 RAG 配置状态。

上传成功返回：

```json
{
  "doc_id": "doc_xxx",
  "title": "文档标题",
  "status": "ready",
  "chunk_count": 12,
  "message": "文档入库完成"
}
```

文档详情返回：

```json
{
  "document": {
    "doc_id": "doc_xxx",
    "title": "文档标题",
    "source_type": ".md",
    "status": "ready",
    "chunk_count": 12,
    "created_at": "...",
    "updated_at": "..."
  },
  "chunks_preview": [
    {
      "chunk_id": "chunk_xxx",
      "chunk_index": 0,
      "content_preview": "...",
      "created_at": "..."
    }
  ]
}
```

统计返回：

```json
{
  "document_count": 3,
  "chunk_count": 42,
  "ready_count": 2,
  "failed_count": 1,
  "rag_sqlite_exists": true,
  "embedding_model_path": "./models/bge-small-zh"
}
```

## v1.5.4 Conversation Archive

会话栏删除使用软归档，不硬删除 JSON 数据。admin/operator 可以归档自己的会话；viewer 返回 403；未登录返回 401。归档后默认列表接口不再返回该记录。

- `POST /api/qa/conversations/{conversation_id}/archive`：归档当前用户自己的 AI 对话记录。
- `POST /api/conversations/{conversation_id}/archive`：归档当前用户自己的 AI 智能体会话记录。

## v1.5.6 QA/RAG 诊断

诊断接口不下载模型、不伪造模型状态、不返回 DeepSeek API Key。

- `GET /api/qa/model-status?include_load_check=false`：查看 bge-small-zh、SQLite RAG、DeepSeek 配置状态；admin/operator/viewer 可用。
- `POST /api/qa/test-embedding`：测试中文向量生成；admin/operator 可用，请求 `{ "text": "测试中文向量生成" }`。
- `POST /api/qa/test-retrieval`：测试当前用户知识库检索；admin/operator 可用，请求 `{ "question": "怎么打爆款？", "top_k": 5 }`。
- `POST /api/qa/diagnose`：返回 summary 和 checks；admin/operator 可用。

## GET /api/agent-runs/{run_id}

查询 agent run 状态，返回进度、日志、结果、错误和文件。

## GET /api/agent-runs

返回当前用户最近任务列表。admin 可使用 `include_legacy=true` 读取旧全局任务。

## POST /api/agent-runs/{run_id}/cancel

软取消 running 任务。已完成或已失败任务返回 400。

## POST /api/agent-runs/{run_id}/retry

基于原任务 payload 创建新的 run。重试会保留 `agent_type`、`mode`、`prompt`、`selected_skill_ids`、`link`、`file_ids`、`image_paths`、`video_path`、`video_url`、`session_id` 和 `workflow_options`。

## GET /api/artifacts/download

下载安全目录内的结果文件。查询参数：`path`。

下载同时执行安全目录和用户归属校验。admin 可访问用户目录及旧安全目录，普通角色只能下载自己的文件。安全目录包括：

- `LOCAL_AGENT_OUTPUT_DIR`
- `apps/api/runtime/artifacts`
- `apps/api/uploads`
- `VIDEO_UPLOAD_DIR`

## GET /api/admin/runtime/health

返回运行时健康状态、版本、服务名和配置 warnings。

## GET /api/admin/runtime/configs/status

返回 `agent_configs`、`skill_templates`、`files` 的存在状态、schema version、数量和 warnings。

## POST /api/admin/runtime/configs/backup

备份当前 runtime configs。

## POST /api/admin/runtime/configs/repair

校验并修复 runtime configs、技能模板和文件记录。损坏文件会移入 corrupted 目录。

## POST /api/admin/runtime/configs/reset

备份当前配置后恢复默认 agent configs 和 skill templates。

## GET /api/admin/runtime/configs/export

导出当前配置、技能模板和文件记录的 JSON 汇总。

## POST /api/admin/runtime/cache/clear

清理可清理运行时缓存，当前包括文件预览缓存。

## GET /api/admin/agent-runs/stats

返回任务总数、各状态数量、超时 running 数量和缺失结果文件数量。

## POST /api/admin/agent-runs/repair-stale

将超过指定分钟数的 running 任务修复为 failed。默认 120 分钟。

## POST /api/admin/agent-runs/cleanup

按天数和状态清理历史任务。`dry_run=true` 时只返回预计数量；实际清理会移动到归档目录。

## GET /api/admin/debug-payloads/{run_id}

查看 local agent 调用保存的 request、response 和 error。

## POST /api/admin/debug-payloads/{run_id}/replay

读取 debug request 并重新调用 local agent，返回 replay_result。

## v1.3 本地 Agent Connector

- `GET /api/agent-connectors`：列出连接器。
- `GET /api/agent-connectors/{connector_id}`：读取连接器。
- `POST /api/agent-connectors`：新增连接器。
- `POST /api/agent-connectors/{connector_id}`：部分更新连接器。
- `DELETE /api/agent-connectors/{connector_id}`：软禁用连接器。
- `POST /api/agent-connectors/{connector_id}/test`：测试 mock、HTTP 或 CLI 连接。
- `POST /api/agent-connectors/{connector_id}/preview-payload`：按指定连接器预览 Payload。
- `POST /api/agent-runs/preview-payload`：按智能体绑定关系预览最终 Payload，不创建任务。
- `GET /api/admin/debug-payloads?limit=&agent_type=&status=`：查询最近联调记录。

以上接口均要求 admin Bearer token；请求和响应中的密码、token、secret 与 API Key 会在 Debug 和 Audit 中脱敏。

## v1.5.6 QA 流式问答

`POST /api/qa/chat/stream`

请求：

```json
{
  "conversation_id": "qa_conv_xxx 或 null",
  "question": "怎么打爆款？",
  "use_rag": true,
  "top_k": 5
}
```

响应：`text/event-stream`

事件：

- `start`：返回 `conversation_id` 和 `message_id`。
- `retrieval_start`：提示正在检索本地知识库。
- `sources`：返回 `sources` 和 `warnings`。
- `delta`：返回增量文本 `{ "text": "..." }`。
- `done`：返回完整回答和消息 ID。
- `error`：返回中文错误信息。

该接口需要登录，admin/operator/viewer 均可使用。`/api/qa/chat` 非流式接口继续保留作为 fallback。

## v1.4 用户管理与审计导出

以下接口均要求 admin Bearer token：

- `GET /api/admin/users`：按 `role`、`enabled`、`keyword`、`limit` 查询用户，不返回密码哈希。
- `POST /api/admin/users`：创建 admin、operator 或 viewer 用户，密码至少 8 位。
- `GET /api/admin/users/{user_id}`：读取单个用户。
- `POST /api/admin/users/{user_id}`：更新角色、启用状态和备注。
- `POST /api/admin/users/{user_id}/enable`：启用用户。
- `POST /api/admin/users/{user_id}/disable`：禁用用户；禁止禁用当前管理员或最后一个启用的管理员。
- `POST /api/admin/users/{user_id}/reset-password`：重置密码并递增 `auth_version`。
- `GET /api/admin/users/{user_id}/agent-runs`：按 `status`、`agent_type` 查看指定用户任务。
- `GET /api/admin/agent-runs`：跨用户查询任务，支持 `user_id`、`status`、`agent_type`、`limit`。
- `GET /api/admin/audit-logs/export`：按现有日志筛选条件导出 `csv` 或 `jsonl` 文件。

角色权限：admin 可访问全部接口；operator 可创建任务、上传文件并操作自己的任务；viewer 仅可查看和下载自己的已有结果。

## v1.5 Dataset 数据清洗

- `GET /api/files?extensions=xlsx,xls,csv&limit=50`：列出当前用户已上传的表格文件。
- `POST /api/datasets/from-file`：根据当前用户的 `file_id` 创建 Dataset 并返回字段建议。
- `GET /api/datasets`：查询当前用户 Dataset；admin 可使用 `include_all_users` 或 `user_id`。
- `GET /api/datasets/mapping-templates`：读取当前用户可复用的字段映射模板。
- `GET /api/datasets/{dataset_id}`：读取 Dataset 元数据。
- `GET /api/datasets/{dataset_id}/preview`：读取前 20 行和字段识别结果。
- `POST /api/datasets/{dataset_id}/field-mapping`：保存字段映射，可同步保存用户模板。
- `GET /api/datasets/{dataset_id}/field-mapping`：读取已保存或建议映射。
- `POST /api/datasets/{dataset_id}/clean`：执行同步清洗并生成 Excel、profile 和 metrics 文件。
- `GET /api/datasets/{dataset_id}/profile`：读取清洗概览。
- `GET /api/datasets/{dataset_id}/files`：读取清洗结果及安全下载地址。
- `DELETE /api/datasets/{dataset_id}`：软删除 Dataset。

`POST /api/agent-runs` 和 Payload 预览支持 `dataset_ids`。通用 workflow 会附加 `dataset_profiles` 和 `dataset_files`；视频脚本拆解协议不接受 Dataset。
