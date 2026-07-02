# Storage SQLite

## 双 SQLite 边界

- APP SQLite 保存平台运行数据：用户、角色、审计、QA 会话、Agent 会话、Agent runs、Connector、Debug Payload、Dataset metadata、file metadata、artifact metadata。
- RAG SQLite 保存知识库 documents、chunks、embedding。

两个 SQLite 独立管理，不合并。

## 默认路径

- APP SQLite: `apps/api/runtime/app/meizhaiseek.sqlite3`
- RAG SQLite: `apps/api/runtime/rag/rag.sqlite3`
- legacy JSON backup: `apps/api/runtime/legacy_json_backups/`
- logs: `apps/api/runtime/logs/`

## Legacy JSON fallback

v1.6.5 默认：

```text
APP_LEGACY_JSON_FALLBACK=false
```

只有紧急恢复旧 JSON 数据时临时设为 `true`。runtime health 会返回 `legacy_json_fallback_enabled`。

## 日志

`start-dev.ps1` 和 `start-dev.bat` 将日志写入：

- `apps/api/runtime/logs/api-dev.log`
- `apps/api/runtime/logs/web-dev.log`

历史日志归档到 `apps/api/runtime/logs/archive/`。日志目录不提交 Git。
