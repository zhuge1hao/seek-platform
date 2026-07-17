# Redis And Queue

## v1.8.4 Acceptance Status

- Redis pause/recovery: `passed`
- Worker crash/restart: `passed`
- Zombie recovery: `passed`
- 50 video jobs: `passed`
- Dataset queue: `not_run`
- Knowledge queue: `not_run`
- Blueprint queue: `not_run`

Redis/RQ is execution infrastructure only. PostgreSQL remains the business state source of truth.

## v1.8.4 P1 Queue Validation - 2026-07-16

Executed:

- Worker crash/restart for `general`, `video`, `knowledge`, `dataset`, and `blueprint`.
- Zombie recovery for stale `running` runs.
- Terminal state protection for `completed`, `failed`, and `cancelled`.
- 50 video jobs: 48 controlled mock jobs and 2 real small-video jobs.
- Redis pause/recovery with API B SSE subscription and DB summary fallback.

Passed:

- `worker-general` x4 and `worker-video` x2 recovered after forced worker kills.
- No tested run stayed permanently `running`.
- Crash/restart runs reached terminal `failed` with queryable errors and `row_version` increments.
- Acceptance jobs produced `0` artifacts, so no duplicate artifacts were generated.
- Final RQ depths after P1 were `queued=0, started=0` for `general`, `video`, `dataset`, `knowledge`, and `blueprint`.
- Video queue max executing was `2`; max queued was `48`.
- Redis pause lasted `1.064s`; DB summary fallback returned the current run state while Redis was paused.
- Redis recovery restored event delivery; no duplicate terminal or duplicate assistant message was observed.

Not executed:

- Dataset `dataset_clean` and `dataset_export` end-to-end queue acceptance.
- Knowledge `document_ingest` and `reindex` end-to-end queue acceptance.
- Blueprint `blueprint_test_run` end-to-end release gate acceptance.

Environment limitation:

- Standalone `worker-dataset`, `worker-knowledge`, and `worker-blueprint` services are not configured. Current production topology has `worker-general` consume `dataset`, `knowledge`, and `blueprint`.

## v1.8.3 Queue Update - 2026-07-12

Encoded:

- Dataset clean enqueue path is covered by unit test.
- QA document upload/reindex and Blueprint test-run enqueue paths remain wired through `tasks.queue.enqueue_call`.
- `worker-general` is confirmed to listen to `general,dataset,knowledge,blueprint`; `worker-video` listens to `video`.

Executed:

- Unit tests for cache_service, redis_service, rate_limit_service, runtime_health_service, agent_run_event_bus, QA document enqueue, Dataset clean enqueue, task queue routing, and Blueprint queue routing.
- Docker queue depth check after service recovery and after the v1.8.3 100-user Locust run.
- 100-user 15-minute Locust rerun with 140 temporary operator accounts.

Passed:

- `python -m unittest discover -s apps/api/tests`: 71 tests OK.
- `python -m pytest apps/api/tests`: 71 passed, 2 skipped.
- Queue depth after Locust recovered to 0 for `general`, `video`, `dataset`, `knowledge`, and `blueprint`.
- Locust 100 users / 15 minutes: 0 failures, aggregate p95 110ms, `/api/agent-runs` p95 370ms, `/api/agents` p95 64ms, login p95 260ms.

Not executed:

- Real worker crash/restart/retry acceptance.
- 50 video job queue acceptance.
- Production Docker end-to-end Dataset/Knowledge/Blueprint job consumption and retry/cancel acceptance.
- Dedicated dataset/knowledge/blueprint worker services.

Not passed:

- Dataset export queue acceptance is not passed because no public Dataset export queue endpoint exists in the current API.

## v1.8.2 Queue Update - 2026-07-10

Encoded:

- Redis clients are now reused per URL/response mode in `redis_service`.
- Redis health errors redact passwords from URLs.
- Cache entries whose keys or nested fields look like secrets/tokens/passwords/API keys are refused.
- QA document upload and reindex enqueue `tasks.knowledge_tasks.execute_document_ingest` when `TASK_QUEUE_BACKEND=redis`; inline/dev mode remains compatible.
- Blueprint test runs enqueue `tasks.blueprint_tasks.execute_blueprint_test` when `TASK_QUEUE_BACKEND=redis`; inline/dev mode keeps the previous immediate Agent Run behavior.
- `worker-general` now listens to `general,dataset,knowledge,blueprint` in production compose. Dedicated dataset/knowledge/blueprint worker services are still not configured.

Executed:

- Unit tests for cache_service, redis_service, rate_limit_service, runtime_health_service, agent_run_event_bus, QA document enqueue, task queue routing, and Blueprint queue routing.
- 100-user 15-minute Locust run on 2026-07-10 with 140 temporary operator accounts.
- Redis queue depth check after Locust.

Passed:

- Queue-related tests passed.
- Locust 100 users / 15 minutes: 0 failures, aggregate p95 120ms, `/api/agent-runs` p95 130ms, `/api/agents` p95 27ms, login p95 210ms.
- Queue depth reached 658 general jobs after Locust, then recovered to 0 after scaling `worker-general` to 4.

Not executed:

- Real worker crash/restart/retry acceptance.
- 50 video job queue acceptance.
- Dataset export queue end-to-end with artifact storage.
- Dedicated dataset/knowledge/blueprint worker services.

v1.8 uses Redis for cache, rate limit, RQ queue, and distributed event wakeups. Redis keys use the `meizhaiseek:` prefix.

Queue modes:

- `TASK_QUEUE_BACKEND=inline`: local development; FastAPI background task executes the run.
- `TASK_QUEUE_BACKEND=redis`: production; `POST /api/agent-runs` returns after creating the run and enqueues worker execution.

Worker entry:

```powershell
python -m workers.worker
```

Current status: Agent Run execution is wired through the queue facade. Dataset/document/Blueprint test run queue migration remains a v1.8 follow-up.
# v1.8.5 Queue Status

- Dataset export enqueue API and Dataset job status/cancel/retry endpoints are coded.
- `apps/api/scripts/acceptance_dataset_queue.py`, `acceptance_knowledge_queue.py`, and `acceptance_blueprint_queue.py` are available for real-stack reruns.
- Real Dataset/Knowledge/Blueprint queue acceptance is `not_run` for v1.8.5 until Docker PostgreSQL/Redis/workers are reachable.
- Redis remains queue/event transport only; PostgreSQL/SQLite app storage is the business state source of truth.
# v1.8.7 Knowledge Queue Evidence

- Knowledge queue is consumed by `worker-general` in the current production compose.
- v1.8.7 acceptance submitted 5 document ingest jobs, all reached `completed` with chunks.
- Reindex job `document-reindex-doc_20260717090831_b87b7459` reached `completed`.
- Queue depth returned to zero after the run.
