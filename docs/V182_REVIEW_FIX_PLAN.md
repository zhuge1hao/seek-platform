# v1.8.2 Review Fix Plan Status

Date: 2026-07-10

## Encoded

- Routers and tests are included in the mypy gate.
- Full `apps/api` mypy now passes.
- Redis client reuse and redacted Redis health errors are implemented.
- Cache refuses sensitive cache keys and nested sensitive fields.
- QA document ingest/reindex and Blueprint test runs have Redis queue entry points.
- Production `worker-general` is configured to consume `general,dataset,knowledge,blueprint`.

## Executed

- P0 tests and push completed in commit `645bea682a54d2ffe670a41631ffbf44f5ad6221`.
- P1 local type/security/unit tests were executed on 2026-07-10.
- BGE-small-zh SQLite and pgvector smoke tests were executed.
- Non-empty pgvector migration smoke was executed with 5 documents and 50 chunks.
- 100-user 15-minute Locust smoke was executed.

## Passed

- Full `mypy apps/api`.
- Bandit medium+.
- pip-audit gate with exact documented exceptions.
- 100-user minimum performance gate.

## Not Passed

- Raw pip-audit without documented exceptions.

## Not Executed

- P2 worker crash/restart.
- P2 50 video jobs.
- P3 200/300/500 users.

## P2 Technical Debt Update - 2026-07-10

Encoded:

- Removed one reviewed B608 site in `conversation_store.list_conversations` by replacing the dynamic archived clause with fixed SQL branches.
- Added tests proving normal Agent and QA conversation append/update paths are incremental and do not bulk-delete existing messages.
- Migrated the remaining simple direct SWR hooks to `useApiQuery`.
- Added Agent Run SSE exponential backoff with jitter, network-online immediate retry, non-retryable 401/403/404 handling, terminal-state stop, and existing polling fallback compatibility.

Executed and passed:

- `python -m pytest apps/api/tests/test_conversation_store.py`: 4 passed.
- `.venv\Scripts\python.exe -m mypy apps/api/services/conversation_store.py apps/api/services/qa_conversation_store.py apps/api/tests/test_conversation_store.py`: passed.
- `npm.cmd run build`: passed.

Not executed:

- Full SQLAlchemy Core migration for all remaining reviewed B608 sites.
- JSON to DB migration for `agent_config_store` and `skill_template_service`.
- P2 worker crash/restart, 50 video jobs, full Dataset/Knowledge/Blueprint Docker worker acceptance, and MinIO TTL/streaming.
