# Capacity Report v1.8/v1.8.4 Update - 2026-07-16

## v1.8.4 Cycle Start Status

- Version under validation: `meizhaiseek v1.8.4`.
- Model display: `meizhaiseek 2.0`.
- 100-user v1.8.4 run: `not_run`.
- 200-user v1.8.4 run: `not_run`.
- 300-user v1.8.4 run: `not_run`.
- 500-user v1.8.4 run: `not_run`.
- Current maximum stable users for v1.8.4: not established.
- Do not reuse older v1.8.3 capacity results as v1.8.4 pass evidence.

# Capacity Report v1.8/v1.8.3 Update - 2026-07-12

Executed:

- 100 users, 15 minutes, Locust 2.32.6, host `http://127.0.0.1`.
- 140 temporary operator accounts were created for `locust_v183_p1_*`; the password was stored only in uncommitted runtime state.
- Running Docker topology included PostgreSQL, Redis, MinIO, API, Web, Nginx, worker-general x4, and worker-video x1.
- `worker-general` listened to `general,dataset,knowledge,blueprint`; no standalone dataset/knowledge/blueprint workers were configured.

First attempt:

- Not passed. PowerShell execution policy prevented loading the runtime Locust environment script, so Locust fell back to the default admin credentials.
- Result: 100 login failures, including 60 HTTP 401 and 40 HTTP 429. This run is excluded from capacity pass conclusions.

Passed minimum gate on rerun:

- Error rate: 0%.
- Total requests: 88,217.
- Aggregate p95: 110ms.
- Aggregate p99: 240ms.
- `/api/agent-runs` submit p95: 370ms.
- `/api/agents` p95: 64ms.
- Login p95: 260ms.
- `/api/conversations` p95: 67ms.
- `/api/qa/health` p95: 170ms.
- `/health` p95: 24ms.
- SSE endpoint p95: 66ms.
- Redis queue depths after the run: `general=0`, `video=0`, `dataset=0`, `knowledge=0`, `blueprint=0`.

Not executed:

- 200-user test.
- 300-user test.
- 500-user test.
- P2 worker crash/restart, MinIO full chain, and 50 video queue tests.

Conclusion:

- v1.8.3 P1 100-user minimum gate passed on current hardware.
- Agent submit p95 <=500ms priority target passed in this run.
- 500-user capacity is still not verified and must not be claimed.

---
# Capacity Report v1.8/v1.8.2 Update - 2026-07-10

Executed:

- 100 users, 15 minutes, Locust 2.32.6, host `http://127.0.0.1`.
- 140 temporary operator accounts were used; admin account sharing was not used for virtual users.
- Running Docker topology included PostgreSQL, Redis, MinIO, API, Web, Nginx, 1 worker-general at start, then worker-general was scaled to 4 for queue drain.

Passed minimum gate:

- Error rate: 0%.
- Aggregate p95: 120ms.
- `/api/agent-runs` submit p95: 130ms.
- `/api/agents` p95: 27ms.
- Login p95: 210ms.
- General queue depth recovered from 658 to 0 after scaling `worker-general=4`.

Observed but not failed for the read-heavy gate:

- `/api/agent-runs/:id/events` p95 was about 1800ms because the Locust task holds the SSE stream for up to 5 seconds.
- `/api/agent-runs/:id/summary` p95 was about 2800ms during queued task backlog.

Not executed:

- 200-user test.
- 300-user test.
- 500-user test.
- P2 worker crash/restart and 50 video queue tests.

Conclusion:

- Current hardware/topology passed the 100-user minimum gate in this run.
- 500-user capacity is not verified and must not be claimed.

---
# Capacity Report v1.8

Status: production validation partially completed. The 20-user baseline passed. The 100-user run completed with 0% errors after using temporary per-user accounts, but latency did not meet the v1.8 capacity targets. The 500-user run was not executed because the 100-user latency gate was not met.

Version: meizhaiseek v1.8
Model name: meizhaiseek 2.0
Validation date: 2026-07-05

## v1.8.2 P1 Addendum

Date: 2026-07-06

Topology used:

- Current Docker production topology through nginx at `http://127.0.0.1`.
- PostgreSQL, Redis, MinIO, API, web, nginx, worker-general x4, worker-video x2 were running before the test.
- External DeepSeek and local 8001 heavy video execution were not part of the Locust mix.
- QA load used `/api/qa/health`.

Preliminary runs:

- Shared admin 100-user 10m: 未通过. 40 `/api/auth/login` requests returned 429 because the single username correctly hit login rate limiting. Aggregate p95 was 73ms, but error rate was not 0%.
- Temporary viewer pool 100-user 10m: 未通过. Login succeeded, but `POST /api/agent-runs` returned 403 because viewers cannot submit runs.

Final P1 run:

- Accounts: 120 temporary `locust_v182_p1_*` operator accounts.
- Command: `locust -f load_tests/locustfile.py --headless -u 100 -r 10 -t 10m --host http://127.0.0.1`.
- Total requests: 54,438.
- Failures: 0.
- Error rate: 0.00%.
- Aggregate p50: 23ms.
- Aggregate p95: 160ms.
- Aggregate p99: 400ms.
- `/api/agents` p95: 99ms.
- Login p95: 320ms.
- Agent submit p95: 600ms.
- `/api/conversations` p95: 110ms.
- `/api/qa/health` p95: 260ms.
- `/health` p95: 38ms.
- SSE events endpoint p95: 120ms.

Conclusion:

- P1 minimum capacity gate: 已通过.
- aggregate p95 <=500ms: 已通过.
- error rate 0%: 已通过.
- Agent submit p95 <=500ms priority target: 未通过.
- P2 distributed acceptance: 未执行 in this addendum.
- P3 200/300/500-user capacity: 未执行.

## v1.8.2 P2 Addendum

Date: 2026-07-06

已执行:

- Redis pause/recovery SSE with two API instances: passed.
- Controlled zombie maintenance repair: passed.

未执行:

- Full worker crash/restart/retry acceptance.
- 50 video queue acceptance.
- Dataset, document ingest, and Blueprint queue acceptance.
- Full MinIO permission/TTL/streaming acceptance.
- pgvector migration dry-run/execute/verify/resume.
- Schema parity.
- 100-user performance retest after all P2 gates.

P3 remains 未执行 because P2 is incomplete.

## Test Machine

- Host: Windows, Docker Desktop
- CPU: Intel Core i5-12400F, 6 cores / 12 logical processors
- Memory: 34 GB physical RAM
- Docker topology: PostgreSQL pgvector, Redis, MinIO, API, web, nginx, worker-general, worker-video
- API profile: `APP_DB_BACKEND=postgres`, `TASK_QUEUE_BACKEND=redis`, `CACHE_BACKEND=redis`, `EVENT_BACKEND=redis`
- DB pool profile: `APP_DB_POOL_SIZE=10`, `APP_DB_MAX_OVERFLOW=5`
- Artifact backend: S3-compatible MinIO
- RAG backend: pgvector

## Production Topology

`docker compose -f docker-compose.prod.yml up -d --build` completed after fixing the web runner path and nginx metrics proxy. Final observed services:

- postgres: running, healthy
- redis: running, healthy
- minio: running, healthy
- api: running, healthy
- web: running, healthy
- nginx: running
- worker-general: running
- worker-video: running

Health checks through nginx:

- `/health`: ok
- `/health/live`: ok
- `/health/ready`: ok
- `/metrics`: reachable

Authenticated runtime health returned:

- `version=v1.8`
- `model=meizhaiseek 2.0`
- `database.backend=postgres`, `database.status=ok`
- `redis.status=ok`
- `queue.backend=redis`, `queue.status=ok`
- `events.backend=redis`
- `artifact_storage.backend=s3`
- `rag.backend=pgvector`
- `capacity_profile=500-users`
- No database URL, PostgreSQL password, S3 secret, or MinIO secret was present in the runtime health JSON.

Warnings still present in runtime health:

- `AUTH_TOKEN_SECRET` is not explicitly set in the local `.env`.
- The local admin password remains the default test password.

## Alembic And PostgreSQL

Real PostgreSQL migration was executed against the Docker PostgreSQL service.

- `alembic current`: executed
- `alembic history`: executed
- `alembic upgrade head`: passed
- repeated `alembic upgrade head`: passed
- final head revision: `20260705_v18_initial`
- table count: 22 application tables plus `alembic_version`
- `CREATE EXTENSION IF NOT EXISTS vector`: passed

Verified application table examples after migration and validation:

- users: 202, including 200 temporary load-test users
- agent_runs: 2865
- agent_conversations: 2845
- agent_messages: 5692
- artifacts: 1296
- datasets: 1
- local_agent_connectors: 5
- agent_blueprints: 1

## SQLite To PostgreSQL Migration

The source SQLite database was backed up to `apps/api/runtime/backups/v18_postgres_migration/`. This runtime backup directory is not intended for commit.

Commands and results:

- Host dry run: passed with `python apps/api/scripts/migrate_sqlite_to_postgres.py --dry-run --json-report`
- Container dry run: failed with SQLite `disk I/O error` on the Windows bind mount; this was not counted as a migration success.
- Host execute: passed with `--execute --batch-size 500 --json-report`
- Host verify: passed with `--verify --json-report`
- Verify summary: 22 tables checked, 0 errors

Verified counts at migration time included:

- users: 2
- agent_runs: 48
- agent_conversations: 28
- agent_messages: 58
- artifacts: 1296
- datasets: 1
- local_agent_connectors: 5
- agent_blueprints: 1
- agent_blueprint_versions: 1
- agent_blueprint_releases: 1

The migration did not delete SQLite, did not silently overwrite conflicts, and did not automatically switch production configuration.

## PostgreSQL Repository Path

`APP_DB_BACKEND=postgres` was validated through the API and runtime health. The core store path now uses the backend-aware DB adapter instead of SQLite-only direct connections.

Validated:

- Login
- Current user
- Conversation reads
- Agent list
- Blueprint list
- Dataset list
- Agent run submit
- Run summary
- Runtime health
- Conversation assistant message backwrite for failed runs

The local 8001 agent service was not running during one RQ validation, so the worker correctly marked the submitted run as failed and wrote the error back to the run/conversation instead of leaving only frontend state.

## Redis, RQ, And Queue

Validated:

- Redis health: ok
- RQ enqueue from API: ok
- Worker consumes queued jobs: ok
- Agent run status/error backwrite: ok
- Runtime health reports Redis queue backend
- Redis rate-limit keys can be cleared for isolated local load tests

Important bottleneck:

- The production compose currently starts one `worker-general` container and one `worker-video` container, both using the single configured RQ queue.
- During the 100-user load test, RQ accumulated hundreds of pending jobs. `rq info` showed 821 queued jobs and 2 executing jobs shortly after the run.
- This does not satisfy the intended v1.8 worker concurrency target of general=4 and video=2 as an actually verified runtime behavior.

Queue-related items not fully validated:

- 50-video-task queue test
- Worker crash/restart/zombie recovery test
- Duplicate enqueue artifact prevention under crash
- Separate measured video concurrency of exactly 2

## MinIO Artifact Storage

Real MinIO validation passed for small samples:

- txt upload/download
- JSON upload/download
- xlsx upload/download
- png upload/download
- SHA-256 checksum validation
- size validation
- content type validation
- object metadata stores `object_key` and does not expose S3 secrets

Validated code path:

- S3-compatible boto3 upload to MinIO
- Streaming download through API-compatible storage facade
- local/local_shared provider remains available for legacy local artifacts

Not fully validated:

- Cross-user artifact ownership via the full UI/API flow
- Video task artifact upload to MinIO under heavy queue load
- Full local artifact migration

## pgvector RAG

Real pgvector validation passed:

- `vector` extension enabled
- pgvector provider writes documents and chunks
- 4 test chunks inserted
- top-k search returned the expected first result
- user/knowledge-base isolation checked
- delete removed vector records
- runtime health reported `rag.backend=pgvector`, `status=ok`

Not fully validated:

- SQLite RAG to pgvector migration on a broader sample
- Long-running document ingest queue under production load

## Automated Regression

Passed:

- `python -m compileall apps/api`
- `python -m unittest discover -s apps/api/tests`: 31 tests
- `python -m pytest apps/api/tests`: 31 passed
- `python apps/api/scripts/verify_sqlite_migration_complete.py`
- `python apps/api/scripts/migrate_sqlite_to_postgres.py --dry-run --json-report`
- `python apps/api/scripts/migrate_sqlite_to_postgres.py --execute --batch-size 500 --json-report`
- `python apps/api/scripts/migrate_sqlite_to_postgres.py --verify --json-report`
- `cd apps/web && npm.cmd ci`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build`
- `docker compose -f docker-compose.prod.yml config`

## Locust Results

The main load test used real nginx, API, PostgreSQL, Redis, RQ, MinIO configuration, and authenticated requests. External DeepSeek/8001 calls were not included in the final baseline; the QA scenario used `/api/qa/health`. Earlier `/api/qa/chat` attempts returned 502 when the external QA dependency was unavailable and were recorded as failed preliminary runs.

### 20 Users

Command:

`locust -f load_tests/locustfile.py --headless -u 20 -r 5 -t 2m --host http://127.0.0.1`

Result: passed, 0 failures.

- Total requests: 1384
- Error rate: 0.00%
- Aggregate p50: 50 ms
- Aggregate p95: 370 ms
- Aggregate p99: 430 ms
- Max: 614 ms
- Login p95: 250 ms
- Agent run submit p95: 410 ms
- `/api/agents` p95: 400 ms
- `/api/conversations` p95: 84 ms
- `/api/qa/health` p95: 120 ms
- SSE smoke p95: 69 ms

This met the 20-user baseline for error rate and most latency targets. `/api/agents` was above the ordinary-read p95 target of 300 ms.

### 100 Users

Initial run with a shared admin account failed 40 login requests with 429 because the username login limiter correctly triggered. Follow-up runs used 200 temporary `loadtest_*` accounts to keep authentication enabled while avoiding the single-username protection.

Command:

`LOCUST_USER_PREFIX=loadtest_ LOCUST_USER_COUNT=200 locust -f load_tests/locustfile.py --headless -u 100 -r 10 -t 5m --host http://127.0.0.1`

First 100-user follow-up result, with the original heavier agent-run mix: completed with 0 failures, but latency did not meet acceptance targets.

- Total requests: 7766
- Error rate: 0.00%
- Aggregate p50: 1200 ms
- Aggregate p95: 4200 ms
- Aggregate p99: 6400 ms
- Agent run submit p95: 5700 ms
- `/api/agents` p95: 6200 ms
- RQ shortly after run: 821 queued jobs, 2 executing jobs

The Locust mix was then adjusted to better match the intended capacity distribution: read-heavy, lower agent-run volume, QA health instead of external QA chat.

Second 100-user follow-up result, weighted baseline:

- Total requests: 8181
- Error rate: 0.00%
- Aggregate p50: 1500 ms
- Aggregate p95: 5400 ms
- Aggregate p99: 8400 ms
- Max: 10279 ms
- Login p95: 2000 ms
- Agent run submit p95: 7800 ms
- Agent run summary p95: 2000 ms
- `/api/agents` p95: 8100 ms
- `/api/conversations` p95: 3500 ms
- `/api/qa/health` p95: 3700 ms
- `/health` p95: 1400 ms
- SSE smoke p95: 2300 ms
- RQ shortly after run: 65 queued jobs, 2 executing jobs

Acceptance result: not passed. The second run showed the problem is not only excessive heavy-task mix; authenticated list routes, synchronous PostgreSQL access, and API concurrency also need tuning.

### 500 Users

Not executed.

Reason: the 100-user run did not meet latency targets. Running 500 users on this host would produce a larger failure sample, not a valid acceptance result.

Required report wording: 500-user test was not completed and must not be reported as passed.

## Capacity Targets

Targets and observed status:

- ordinary reads p95 < 300 ms: not met at 100 users
- login p95 < 500 ms: not met at 100 users
- task submit p95 < 500 ms: not met at 100 users
- SSE establish p95 < 1 s: not met at 100 users
- SSE status propagation p95 < 2 s: approximate smoke p95 2.1 s at 100 users, not met
- ordinary API error rate < 1%: met at 20 and 100 users after per-user accounts
- task submit success rate > 99%: met at 100 users by HTTP response, but queue depth grew and completion capacity was not proven

## Bottlenecks

- RQ worker runtime concurrency was below the intended v1.8 target. Only two workers were observed processing a single shared queue.
- Agent run submission created queue depth in both 100-user samples; the first sample accumulated hundreds of jobs, and the weighted sample still left queued jobs.
- `/api/agents` response payload and/or cache path remained too slow under 100 concurrent authenticated users.
- Synchronous PostgreSQL adapter opens many short-lived database operations and needs pooling/profiling before another capacity run.
- Login and even `/health` were above target under 100 users on this host, indicating broader API saturation.
- The current local host and Docker Desktop setup is not a verified 500-user production environment.

## Not Executed Or Not Complete

- 500-user Locust run
- 100 and 500 dedicated SSE connection tests
- 50-video-task queue test with measured video concurrency of 2
- Worker crash, restart, retry, and zombie recovery validation
- Multi API instance Redis Pub/Sub SSE validation
- Nginx multi-instance load-balancing validation
- Full S3/MinIO ownership validation through the UI
- Full pgvector migration from SQLite RAG
- Dataset clean/export queue validation at load
- Document ingest queue validation at load
- Blueprint test run queue validation at load

## Recommendations

Before another 100/500-user run:

- Run at least 4 general worker processes and 2 video worker processes, or scale compose services explicitly and verify `rq info`.
- Split queues by workload class: general, video, dataset, document, blueprint.
- Reduce agent-run percentage in the main capacity mix, and run heavy agent/video workflows in a separate queue stress test.
- Add cache validation and profiling for `/api/agents` and other list endpoints.
- Track queue depth, active workers, DB active connections, Redis latency, API CPU, and API memory during each Locust run.
- Re-run 100 users after worker scaling and endpoint tuning; execute 500 only after 100 users meets the latency targets.

## v1.8.1 Security And 100-User Performance Update

Date: 2026-07-06.

Version under test: meizhaiseek v1.8.1, model name meizhaiseek 2.0.

Implemented changes:

- Removed production fallback to a public fixed JWT secret. Production now requires `AUTH_TOKEN_SECRET`; local development may generate a runtime-only secret.
- Rotated the existing production admin account away from `admin123`; old password returned 401 and the generated strong password returned 200. The generated value is stored only in local uncommitted `.env`.
- Added `table_count` table-name allowlisting.
- Replaced local CLI agent `shell=True` execution with validated argument lists.
- Added non-secret logging for Redis/cache/legacy preview fallback paths.
- Added a small psycopg connection pool for the sync PostgreSQL adapter.
- Optimized `/api/agents` with a lightweight batched query path and short TTL cache.
- Moved successful login and agent-submit audit writes off the response path where safe.
- Returned `queue_job_id` from agent run submit and split RQ queue selection into `general`, `video`, `dataset`, `knowledge`, and `blueprint`.
- Scaled production compose for this run to `worker-general=4` and `worker-video=2`.
- Fixed Nginx Docker DNS behavior after API container recreation by adding Docker resolver-based upstreams.

### v1.8.1 Validation Commands

- `python -m compileall apps/api`: passed.
- `python -m unittest discover -s apps/api/tests`: passed, 35 tests.
- `python -m pytest apps/api/tests`: passed, 35 tests.
- `docker compose -f docker-compose.prod.yml config --quiet`: passed.
- `docker compose -f docker-compose.prod.yml up -d --build --scale worker-general=4 --scale worker-video=2`: passed.
- `/health`, `/health/live`, `/health/ready`: passed through the Nginx entry after Nginx restart.

### v1.8.1 20 Users

Command:

`locust -f load_tests/locustfile.py --headless -u 20 -r 5 -t 2m --host http://127.0.0.1`

Result: passed, 0 failures.

- Total requests: 2469
- Error rate: 0.00%
- Aggregate p50: 7 ms
- Aggregate p95: 44 ms
- Aggregate p99: 83 ms
- `/api/agents` p95: 19 ms
- Login p95: 110 ms
- Agent run submit p95: 120 ms
- Conversation list p95: 17 ms
- Queue depth after run: 0

### v1.8.1 100 Users

The first 100-user v1.8.1 run reused a single admin account and correctly triggered username login rate limiting: 40 login requests returned 429. That run is not counted as a capacity pass because the test data setup was wrong.

Temporary users `loadtest_v181_0` through `loadtest_v181_99` were then created with a generated strong password stored only in local uncommitted `.env`.

Preheat command:

`LOCUST_USER_PREFIX=loadtest_v181_ LOCUST_USER_COUNT=100 locust -f load_tests/locustfile.py --headless -u 100 -r 10 -t 2m --host http://127.0.0.1`

Preheat result: passed, 0 failures.

- Total requests: 11399
- Error rate: 0.00%
- Aggregate p50: 17 ms
- Aggregate p95: 140 ms
- Aggregate p99: 300 ms
- `/api/agents` p95: 87 ms
- Login p95: 300 ms
- Agent run submit p95: 490 ms

Formal command:

`LOCUST_USER_PREFIX=loadtest_v181_ LOCUST_USER_COUNT=100 locust -f load_tests/locustfile.py --headless -u 100 -r 10 -t 10m --host http://127.0.0.1`

Formal result: passed the P1 minimum gate, 0 failures.

- Total requests: 57473
- Error rate: 0.00%
- Aggregate p50: 19 ms
- Aggregate p95: 140 ms
- Aggregate p99: 310 ms
- Max: 978 ms
- `/api/agents` p95: 87 ms
- Login p95: 330 ms
- Agent run submit p95: 520 ms
- Agent run events p95: 92 ms
- Agent run summary p95: 94 ms
- Conversation list p95: 96 ms
- QA health p95: 220 ms
- `/health` p95: 32 ms
- Queue depth during run: short spikes observed, including 6-7 general jobs; queue returned to 0.
- Observed resource pressure: API roughly 75-114% CPU, PostgreSQL roughly 72-90% CPU, general workers roughly 130-200% CPU each during snapshots; memory remained stable.

Acceptance result:

- P1 minimum gate passed: error rate < 1%, aggregate p95 <= 1000 ms, `/api/agents` p95 <= 1000 ms, login p95 <= 1000 ms, agent submit p95 <= 1000 ms.
- Priority target mostly passed. Agent submit p95 was 520 ms in the formal 10-minute run, slightly above the 500 ms priority target but far below the minimum gate.

### v1.8.1 Distributed SSE Smoke

API A: production Docker/Nginx on port 80/8000.

API B: local uvicorn on `127.0.0.1:8002`, configured for the same PostgreSQL, Redis, S3, and pgvector backends.

Result: passed smoke validation.

- API A created run `run_20260706064511_960a042b`.
- API B subscribed to `/api/agent-runs/{run_id}/events`.
- API B received 11 SSE events.
- Final run status was `failed` because the external workflow failed, but status and error propagation through PostgreSQL/Redis/SSE worked.
- SSE payload leak check passed: no `raw_response`, no full prompt, no `workflow_options`, no token.

Full API restart/failover, Redis pause/recovery, and 100/500 dedicated SSE connection tests remain not executed.

### v1.8.1 Not Executed

- 200-user, 300-user, and 500-user P3 tests: not executed in this pass.
- Worker crash/restart with real killed worker process: not executed.
- 50-video-task queue concurrency test: not executed.
- Dataset clean/export queue acceptance: not executed.
- Document ingest queue acceptance: not executed.
- Blueprint test run queue acceptance: not executed.
- Full S3 signed URL expiration and large-file streaming test: not executed.
- Full SQLite RAG to pgvector resumable migration: not executed.

### v1.8.1 Quality And Security Follow-up

- Dependency hardening: upgraded FastAPI to 0.139.0, python-multipart to 0.0.32, requests to 2.34.2, pytest to 9.1.1, and pytest-asyncio to 1.4.0. `pip check` passed.
- `pip-audit` after upgrade: 3 remaining advisories in `transformers 4.57.6`; not fixed because current `sentence-transformers 3.3.1` constrains `transformers<5`.
- `ruff check apps/api`: passed.
- `bandit -r apps/api -x apps/api/tests,apps/api/runtime,apps/api/models`: not fully passed; high severity count is 0. Remaining findings are 25 medium and 5 low, mainly dynamic SQL-fragment false positives/review-needed spots and guarded `subprocess` use.
- Scoped `mypy`: not passed. Current package layout needs mypy path/config work and targeted type fixes before it can become a blocking CI gate.
- Production rebuild after dependency upgrade: passed. Runtime health confirmed `version=v1.8.1`, Postgres, Redis, queue, S3, and pgvector healthy.
