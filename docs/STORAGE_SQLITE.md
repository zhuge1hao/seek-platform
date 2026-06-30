# APP SQLite 存储说明

## 目标

v1.5.7 新增 APP SQLite，用于替代平台运行数据中的 JSON 临时存储。该迁移不改变前端接口结构，也不迁移 RAG 知识库向量数据。

## 两个 SQLite 的边界

- APP SQLite：`APP_SQLITE_PATH`，默认 `apps/api/runtime/app/meizhaiseek.sqlite3`。保存用户、审计、QA 会话、AI 智能体会话、agent runs、Connector、Debug Payload、文件和 artifact metadata。
- RAG SQLite：`RAG_SQLITE_PATH`，默认 `apps/api/runtime/rag/rag.sqlite3`。保存知识库 documents、chunks 和 embedding。

两个数据库独立存在，不能合并。RAG SQLite 不保存账号和任务运行状态，APP SQLite 不保存 embedding。

## 主要表

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

所有 JSON 类型字段均以 JSON 字符串保存，时间字段统一使用 ISO 字符串。

## JSON 迁移流程

1. 服务启动时执行 `init_app_db()` 和 `run_migrations()`。
2. 如果 `APP_SQLITE_AUTO_MIGRATE=true`，并且 `app_kv.json_migration_completed` 不是 true，则执行 JSON 迁移。
3. 迁移前复制旧 JSON/JSONL 到 `APP_JSON_LEGACY_BACKUP_DIR/{timestamp}`。
4. 使用原始 ID 幂等写入 SQLite，重复执行不会重复插入。
5. 单条坏数据记录到迁移报告的 `errors`，未知 JSON 记录到 `skipped`。
6. 迁移报告写入 `app_kv.json_migration_report`。

## 手动迁移

管理员可以调用：

```http
POST /api/admin/storage/migrate-json
Authorization: Bearer <token>
```

该接口会再次备份 legacy JSON，并返回迁移报告。

## 健康检查

管理员可以调用：

```http
GET /api/admin/storage/health
Authorization: Bearer <token>
```

返回 APP SQLite 路径、表计数、迁移状态和最近备份目录。

## 回滚说明

旧 JSON 文件不会被删除。若需要排查或回滚，可以从 `apps/api/runtime/legacy_json_backups` 找到迁移前备份，并结合 `app_kv.json_migration_report` 查看迁移计数和错误。回滚时应先停止服务，再手动恢复目标 JSON 文件。

## 常见问题

- APP SQLite 文件不存在：检查 `APP_SQLITE_PATH` 是否可写，并重启后端。
- 迁移报告有 errors：查看具体文件和错误项，修复坏 JSON 后手动触发迁移。
- RAG 检索无 sources：检查 RAG SQLite 是否有当前用户 chunks，该问题与 APP SQLite 无关。
- 用户无法登录：检查 `users` 表是否迁移成功，确认 `is_enabled` 和 `auth_version` 未被异常修改。

## v1.5.8 Dataset metadata 与增量写入

- APP SQLite 新增 `datasets`、`dataset_files`、`dataset_jobs`，保存 Dataset metadata、字段映射、清洗规则、profile、metrics 和结果文件路径。
- Dataset 原始 Excel、图片和清洗导出文件仍保存在磁盘目录，不写入 SQLite 二进制内容。
- QA conversation 与 Agent conversation 的日常写入改为增量 upsert；bulk replace 仅用于 legacy JSON migration。
- `service_events` 提供本地轻量 run updated 事件，`task_store` 写入 run 后发事件，由 conversation store 同步 assistant message 状态。
- APP SQLite 与 RAG SQLite 边界不变：RAG SQLite 仍只保存知识库 documents/chunks/embedding。