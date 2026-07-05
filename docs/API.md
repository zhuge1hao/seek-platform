# API

本文档记录 meizhaiseek v1.7.2 的主要后端接口。除 `/health` 和登录接口外，业务接口默认需要 `Authorization: Bearer <token>`。

## Agent Blueprint v1.7.2 增强接口

- `GET /api/agent-blueprints/{blueprint_id}/versions/diff?from_version_id=&to_version_id=`：返回稳定 JSON 版本差异，Prompt 差异仅作为响应展示，不写入审计明细。
- `GET /api/agent-blueprints/{blueprint_id}/validations`：查询验证历史。viewer 不可访问。
- `GET /api/agent-blueprints/{blueprint_id}/validations/{validation_id}`：查询单次验证结果。
- `POST /api/agent-blueprints/{blueprint_id}/release-gate`：检查当前版本发布门禁，返回 `allowed`、`blocking_errors`、`warnings`、`validation_id`、`test_run_id`。
- `GET /api/agent-blueprints/{blueprint_id}/test-runs?limit=20`：查询测试运行历史。
- `GET /api/agent-blueprints/{blueprint_id}/test-runs/{test_run_id}`：查询单次测试运行详情。
- `POST /api/agent-blueprints/{blueprint_id}/preview/input`：根据 input schema 返回结构预览，不读取本地文件、不提交任务。
- `POST /api/agent-blueprints/{blueprint_id}/preview/result`：根据 output schema 和 result UI config 返回结构预览。
- `POST /api/agent-blueprints/{blueprint_id}/publish`：新增 `confirm_warnings` 参数；后端重新执行发布门禁，blocking error 返回 `409`。
- `GET /api/agents`：增加轻量蓝图字段 `blueprint_last_test_status`、`blueprint_methodology_summary`、`blueprint_output_summary`；不返回 Prompt、完整 methodology 或 execution config。

## Health

`GET /health`

```json
{"status":"ok","service":"meizhaiseek-api"}
```

`GET /api/admin/runtime/health`

仅管理员可用。返回运行时版本、存储状态、安全配置提示、legacy fallback 状态等。v1.7.2 返回：

```json
{
  "service": "meizhaiseek-api",
  "version": "v1.7.2",
  "legacy_json_fallback_enabled": false,
  "warnings": []
}
```

## Auth

- `POST /api/auth/login`: 用户名密码登录，返回 token 和当前用户。
- `POST /api/auth/logout`: 记录退出审计。
- `GET /api/auth/me`: 校验 token、用户状态和 `auth_version`。
- `POST /api/auth/change-password`: 当前用户修改密码。

## Admin

- `GET /api/admin/users`: 查询用户。
- `POST /api/admin/users`: 创建用户。
- `GET /api/admin/users/{user_id}`: 读取用户详情。
- `POST /api/admin/users/{user_id}`: 更新角色、启用状态和备注。
- `POST /api/admin/users/{user_id}/enable`: 启用用户。
- `POST /api/admin/users/{user_id}/disable`: 停用用户。
- `POST /api/admin/users/{user_id}/reset-password`: 重置密码。
- `GET /api/admin/audit-logs`: 查询审计日志。
- `GET /api/admin/audit-logs/export`: 导出审计日志。

## AI 对话

- `GET /api/qa/conversations`: QA 会话列表。
- `GET /api/qa/conversations/{conversation_id}`: QA 会话详情。
- `POST /api/qa/conversations`: 创建 QA 会话。
- `POST /api/qa/conversations/{conversation_id}/archive`: 归档 QA 会话。
- `POST /api/qa/chat`: 非流式问答，DeepSeek 调用通过 async wrapper 执行。
- `POST /api/qa/chat/stream`: SSE 流式问答，保持稳定主链路。
- `GET /api/qa/knowledge/stats`: 知识库统计。
- `GET /api/qa/knowledge/documents`: 知识库文档列表。
- `GET /api/qa/model-status`: 本地模型、RAG、DeepSeek 配置状态。

## AI 智能体

- `GET /api/agents`: 智能体注册信息。v1.7 增加 `blueprint_id`、`blueprint_status`、`blueprint_version`、`blueprint_published`；没有蓝图的现有智能体返回 `blueprint_status=unmanaged`。
- `GET /api/agent-configs`: 智能体配置列表。
- `GET /api/agent-configs/{agent_type}`: 单个智能体配置。
- `POST /api/agent-configs/{agent_type}`: 更新智能体配置。
- `GET /api/skills/templates`: 技能模板列表。
- `POST /api/skills/templates`: 创建或更新技能模板。

## Agent Blueprint API

蓝图接口默认需要登录。`admin` 可执行全部操作；`operator` 可查看、创建草稿、编辑草稿、创建版本、运行测试、复制和导出；`viewer` 只能查看已发布蓝图和已发布版本，且不能查看未发布 Prompt。

- `GET /api/agent-blueprints`: 蓝图列表。
- `POST /api/agent-blueprints`: 创建 draft 蓝图并创建初始版本。
- `GET /api/agent-blueprints/{blueprint_id}`: 蓝图详情、当前版本、发布版本、测试用例和 release 记录。
- `PATCH /api/agent-blueprints/{blueprint_id}`: 更新未发布蓝图基础信息。
- `DELETE /api/agent-blueprints/{blueprint_id}`: 删除未发布 draft。
- `POST /api/agent-blueprints/{blueprint_id}/versions`: 创建新版本。
- `GET /api/agent-blueprints/{blueprint_id}/versions`: 版本列表。
- `GET /api/agent-blueprints/{blueprint_id}/versions/{version_id}`: 指定版本。
- `POST /api/agent-blueprints/{blueprint_id}/validate`: 返回 `{valid, errors, warnings}`。
- `POST /api/agent-blueprints/{blueprint_id}/publish`: 管理员发布版本。
- `POST /api/agent-blueprints/{blueprint_id}/rollback`: 管理员回滚到历史已发布版本，并生成新版本。
- `POST /api/agent-blueprints/{blueprint_id}/clone`: 复制为 draft 蓝图。
- `POST /api/agent-blueprints/{blueprint_id}/disable`: 停用蓝图。
- `POST /api/agent-blueprints/{blueprint_id}/enable`: 重新启用蓝图。
- `POST /api/agent-blueprints/{blueprint_id}/deprecate`: 废弃蓝图。
- `GET /api/agent-blueprints/{blueprint_id}/test-cases`: 测试用例列表。
- `POST /api/agent-blueprints/{blueprint_id}/test-cases`: 创建测试用例。
- `PATCH /api/agent-blueprints/{blueprint_id}/test-cases/{test_case_id}`: 更新测试用例。
- `POST /api/agent-blueprints/{blueprint_id}/test-cases/{test_case_id}/run`: 复用 Agent Run 创建真实测试 run。
- `GET /api/agent-blueprints/{blueprint_id}/releases`: 发布、回滚、停用、启用、废弃记录。
- `GET /api/agent-blueprints/{blueprint_id}/export`: 导出脱敏 JSON。
- `POST /api/agent-blueprints/import/preview`: 导入预览，不写库。
- `POST /api/agent-blueprints/import`: 正式导入；冲突时默认生成新蓝图 ID。

蓝图状态枚举：`draft | testing | published | disabled | deprecated`。执行类型枚举：`internal | http_connector | cli_connector | mock`。结果 renderer 枚举：`generic_text | generic_structured | video_breakdown | table_report | dataset_report`。

## 会话与任务

- `GET /api/conversations`: 当前用户智能体会话列表。
- `GET /api/conversations/{conversation_id}`: 会话详情、消息和 latest run。
- `POST /api/conversations`: 创建会话。
- `POST /api/conversations/{conversation_id}/rename`: 重命名会话。
- `POST /api/conversations/{conversation_id}/archive`: 归档会话。
- `POST /api/agent-runs`: 提交智能体任务。
- `GET /api/agent-runs/{run_id}/summary`: 轻量任务摘要，用于轮询或 SSE fallback。
- `GET /api/agent-runs/{run_id}/result`: 完整任务结果。
- `POST /api/agent-runs/{run_id}/cancel`: 取消任务。
- `POST /api/agent-runs/{run_id}/retry`: 创建重试任务。
- `POST /api/agent-runs/preview-payload`: 预览最终提交 payload。

## Agent Run SSE

`GET /api/agent-runs/{run_id}/events`

需要登录，且只能订阅自己的 run。前端使用 fetch stream 携带 Bearer token。事件格式：

```text
event: status
data: {"run_id":"run_xxx","status":"running","progress":20}
```

支持事件：`status`、`step`、`completed`、`failed`、`heartbeat`。终态后服务端关闭流。SSE 失败时前端回退到 `GET /summary` 轮询。

## 视频拆解 Agent

`GET /api/agents/video-script/status`

后端通过 Connector 请求本地视频 Agent `/health`，返回 `connected/disconnected/disabled/mock`、`status`、`service`、`version`、`model_version`、`latency_ms` 等字段。8001 不可达时返回 disconnected，不返回 500。

`POST /api/agent-runs` 使用 `agent_type=video_script_breakdown` 时，平台将参数映射为本地 Agent `/run` payload：

```json
{
  "mode": "shot_text_excel",
  "video_file": "E:\\USE\\codexhome\\fenge\\videos\\test\\1.mp4",
  "output_dir": "E:\\USE\\codexhome\\fenge\\output\\test",
  "subtitle_region": "bottom",
  "ocr_workers": 6
}
```

`result_json.summary` 标准字段包括：`video_name`、`video_path`、`status`、`raw_shot_count`、`model_optimized_shot_count`、`excel_column_count`、`excel_image_count`、`artifact_count`、`excel_path`、`shot_report_path`、`execution_mode`。

## Connector 与 Debug Payload

- `GET /api/agent-connectors`: Connector 列表。
- `GET /api/agent-connectors/{connector_id}`: Connector 详情。
- `POST /api/agent-connectors`: 创建 Connector。
- `POST /api/agent-connectors/{connector_id}`: 更新 Connector。
- `DELETE /api/agent-connectors/{connector_id}`: 停用 Connector。
- `POST /api/agent-connectors/{connector_id}/test`: 测试 Connector。
- `GET /api/admin/debug-payloads`: Debug Payload 列表。
- `GET /api/admin/debug-payloads/{run_id}`: Debug Payload 详情。
- `POST /api/admin/debug-payloads/{run_id}/replay`: replay 保存的 request，不覆盖原始 run。

## Dataset、文件与 Artifact

- `POST /api/files/upload`: 通用文件上传。
- `GET /api/files`: 当前用户文件列表。
- `GET /api/files/{file_id}/preview`: 文件预览。
- `POST /api/datasets/from-file`: 从文件创建 Dataset。
- `GET /api/datasets`: Dataset 列表。
- `GET /api/datasets/{dataset_id}`: Dataset 元数据。
- `GET /api/datasets/{dataset_id}/preview`: Dataset 预览。
- `POST /api/datasets/{dataset_id}/clean`: 执行清洗。
- `GET /api/datasets/{dataset_id}/files`: Dataset 输出文件。
- `GET /api/agent-runs/{run_id}/artifacts/{artifact_id}/download`: 按 user/run 校验下载 artifact。



## v1.7.2 API additions

### Runtime health

`GET /api/admin/runtime/health` returns `version: v1.7.2` and includes `legacy_json_fallback_enabled`, `legacy_json_fallback_usage_count`, `legacy_json_fallback_last_used_at`, `async_store: { enabled, max_concurrency }`, and `agent_run_events: { transport: "sse", polling_fallback: true, event_hub: true }`. Sensitive secrets are not returned.

### Registry sync

`GET /api/agent-blueprints/registry-sync/preview` is available to operator/admin users and reports registry-only, blueprint-only, matched, conflict, disabled, and deprecated bindings.

`POST /api/agent-blueprints/registry-sync/apply` is admin-only. Body: `{ "agent_ids": ["..."], "create_as": "draft" }`. It only creates draft Blueprints for registry-only agents and never publishes or overwrites existing published Blueprints.

### Agent Run events

Agent Run SSE remains the primary realtime channel. v1.7.2 adds an in-process Event Hub so SSE can react to task_store updates before heartbeat polling. SQLite remains the source of truth and polling fallback remains supported.

### Blueprint release E2E

The default release E2E test uses mock/internal execution and does not require DeepSeek, BGE, or the local 8001 Connector. The optional video Blueprint E2E remains separate.
