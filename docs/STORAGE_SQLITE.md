# Storage SQLite

## 双 SQLite 边界

- APP SQLite 保存平台运行数据：用户、角色、审计、QA 会话、Agent 会话、Agent runs、Connector、Debug Payload、Dataset metadata、file metadata、artifact metadata。
- RAG SQLite 保存知识库 documents、chunks、embedding。

两个 SQLite 独立管理，不合并。

v1.8 保留 SQLite 作为本地开发默认后端。生产推荐 PostgreSQL，但不进行 SQLite/PostgreSQL 双写；通过 `APP_DB_BACKEND=sqlite|postgres` 选择目标后端。

## Agent Blueprint 表

v1.7 新增 APP SQLite 表：`agent_blueprints`、`agent_blueprint_versions`、`agent_blueprint_test_cases`、`agent_blueprint_releases`。这些表只保存蓝图描述、版本、测试用例和发布记录，不改变 RAG SQLite 边界，也不引入外部数据库。

## 默认路径

- APP SQLite: `apps/api/runtime/app/meizhaiseek.sqlite3`
- RAG SQLite: `apps/api/runtime/rag/rag.sqlite3`
- legacy JSON backup: `apps/api/runtime/legacy_json_backups/`
- logs: `apps/api/runtime/logs/`

## Legacy JSON fallback

v1.7 默认：

```text
APP_LEGACY_JSON_FALLBACK=false
```

只有紧急恢复旧 JSON 数据时临时设为 `true`。runtime health 会返回 `legacy_json_fallback_enabled`。

## 日志

`start-dev.ps1` 和 `start-dev.bat` 将日志写入：

- `apps/api/runtime/logs/api-dev.log`
- `apps/api/runtime/logs/web-dev.log`

历史日志归档到 `apps/api/runtime/logs/archive/`。日志目录不提交 Git。

v1.7.2 追加 APP SQLite 表：`agent_blueprint_test_runs`、`agent_blueprint_validation_results`。它们只保存蓝图测试运行历史和验证历史，不改变 APP SQLite 与 RAG SQLite 的边界。

## v1.8 SQLite migration

v1.8 追加 APP SQLite schema marker `20260705_v18_capacity_foundation`：

- `agent_runs.row_version`：用于 worker 并发和终态保护。
- `artifacts.storage_backend`、`object_key`、`original_filename`、`checksum`：兼容 local artifact，并为 `local_shared`/`s3` provider 预留元数据。

迁移脚本：

```powershell
python apps/api/scripts/migrate_sqlite_to_postgres.py --dry-run --json-report
python apps/api/scripts/migrate_sqlite_to_postgres.py --verify
python apps/api/scripts/migrate_sqlite_to_postgres.py --execute --verify
```

脚本在 execute 前备份 SQLite，不删除源库，不静默覆盖冲突。

## meizhaiseek v1.7.2

v1.7.2 focuses on architecture stabilization after the 2026-07-03 evaluation: Blueprint release E2E coverage, wider auth/conversation/task tests, Blueprint Store splitting, legacy JSON fallback retirement diagnostics, production Docker build/start, Agent Run SSE tests, async SQLite read wrappers, frontend API module compatibility split, methodology drag ordering, Registry/Blueprint reconciliation, and the Agent Run Event Hub. Existing Agent, Workflow, Connector, APP SQLite, RAG SQLite, Dataset, QA/RAG, Debug Payload, and video breakdown execution models are unchanged.
