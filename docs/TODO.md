# TODO
## v1.8.10 Active Items

- `coded`: Agent submit atomic persistence, pre-generated queue job id, incremental conversation writes, transaction budget headers, and database latency metrics.
- `not_run`: v1.8.10 production profile, PostgreSQL durability/worker comparison, 100-user and 200-user gates.
- `out_of_scope`: 300/500-user load tests, local video Agent changes, and broad frontend work.

## v1.8.9 Closed Items

- `coded`: runtime version updated to `v1.8.9`; smoke version checks now support CLI/env/config precedence; PostgreSQL pool metrics are wired.
- `passed`: browser full production matrix, multi-instance SSE production acceptance, Redis recovery, live pool metrics collection, smoke_minimal, and the 100-user regression.
- `failed`: 200-user capacity gate after three rounds; final submit p95 was `1800 ms`, above the `1000 ms` gate.
- `not_run`: 300/500-user capacity tests, by v1.8.9 scope.
- Current maximum stable users: `100`.

## v1.8.7 Priority

- Done: Knowledge queue acceptance passed.
- Done: MinIO permission, TTL, 10MB streaming, 100MB streaming, and user-isolation acceptance passed.
- Done: pgvector resume and top-k comparison evidence passed.
- Done: pip-audit accepted-risk recheck passed through the exact exception gate; raw pip-audit still fails.
- Done: 100-user baseline passed.
- Remaining: complete browser `/agent` video/download/cancel/retry checks before setting the full browser marker to `passed`.
- Deferred: keep 200/300/500-user tests out of v1.8.7.

## v1.8.6 Priority

- Validate Dataset, Knowledge, and Blueprint business queues end to end through Redis/RQ and worker-general.
- Validate MinIO permissions, TTL, streaming, user isolation, and artifact HTTP downloads.
- Validate pgvector non-empty migration, resume, idempotency, and top-k comparison.
- Run real browser `/agent` smoke for Run-card refresh, conversation list refresh, cancel/retry, and user isolation.
- Close runtime health markers only for items with real command evidence.
- Keep 200/300/500-user capacity tests out of v1.8.6; do not claim 500 users without a later real run.

## v1.8.4 Priority

- Commit the v1.8.3 `/agent` run-card/conversation-refresh frontend fix cleanly.
- Validate real 8001 video Agent E2E through backend, Redis/RQ, worker-video, artifacts, SSE, and frontend restore.
- Validate worker crash/restart, zombie recovery, 50 video jobs, and Redis pause/recovery.
- Validate Dataset, Knowledge, Blueprint queues and pgvector non-empty migration with resume.
- Validate MinIO permissions/TTL/streaming, backup recovery, Docker runtime health, and 100/200/300/500-user capacity gates.
- Record unexecuted items as `not_run` and failed gates as `failed`.

## v1.8.3 Priority

- Re-verify full `mypy apps/api`; fix only real regressions.
- Complete remaining `_PostgresPool` edge tests without replacing the pool.
- Prove QA/Knowledge, Dataset, and Blueprint queue paths through Redis/RQ.
- Run pgvector non-empty migration validation with isolated test data.
- Keep P3 capacity tests blocked until P2 critical production acceptance passes.

## v1.8 completed

- PostgreSQL/Alembic schema foundation.
- SQLite to PostgreSQL migration script.
- Redis/cache/rate-limit/distributed event bus foundation.
- Inline/RQ queue facade and worker entry.
- Agent Run `row_version` and terminal status guards.
- `/health/live`, `/health/ready`, runtime health v1.8 component status.
- Artifact storage provider facade and checksum metadata.
- RAG provider facade.
- Docker production topology.
- Locust baseline script.
- v1.8 production, capacity, migration, queue, storage, RAG, realtime, and observability docs.

## v1.8 remaining verification

- Run `alembic upgrade head` against real PostgreSQL.
- Verify Redis Pub/Sub cross-instance SSE.
- Verify RQ worker retry, timeout, cancellation, idempotency, and zombie recovery.
- Finish actual S3 upload provider and mock/provider tests.
- Finish pgvector provider migration or keep reporting it as not migrated.
- Run Locust 20/100/500 levels on real hardware and record honest results.

## v1.7.2 completed

- Blueprint visual editor and structured sections.
- Blueprint test runs, validation history, version diff, release gate, publish, rollback, and Registry Sync.
- `/agent` Blueprint summary display.
- Blueprint SWR hooks and automated tests.
- Store/API/module splitting, Agent Run Event Hub, Docker production cleanup, and docs.

## later ideas

- Reference-project breakdown and Blueprint generation assistant.
- First non-video business agent based on Blueprint governance.
- Multi-agent workflow orchestration.
- Continue moving low-risk read APIs to SWR.
- Keep legacy JSON fallback disabled unless emergency recovery is needed.
- Add more video breakdown failure and artifact boundary tests.
