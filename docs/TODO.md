# TODO

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