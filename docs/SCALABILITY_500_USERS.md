# Scalability 500 Users
## v1.8.9 Gate Update

This cycle executed the 200-user gate after the browser matrix, multi-instance SSE, Redis recovery, pool metrics, Docker health, and 100-user baseline prerequisites passed. The 200-user gate remained `failed` after three rounds because `/api/agent-runs` submit p95 stayed above the `1000 ms` limit. 300/500-user load tests remain out of scope and stayed `not_run`.

- 100 users: `passed` on 2026-07-19, round 2.
- 200 users: `failed` on 2026-07-19 after three rounds.
- 300 users: `not_run`.
- 500 users: `not_run`.
- Current maximum stable users: `100`.
- Latest 200-user round: 100,301 requests, 0 failures, aggregate p95 `490 ms`, p99 `920 ms`, submit p95 `1800 ms`, pool-wait p95 `0.000953807 s`, DB pool timeout `0`, final queue depth `0`.

## v1.8.7 Capacity Status

- 100 users: `passed` on 2026-07-17.
- 200 users: `not_run`.
- 300 users: `not_run`.
- 500 users: `not_run`.
- Current maximum stable users: `100`.

Do not claim 500-user support unless the real 500-user Locust command passes and is recorded in `docs/CAPACITY_REPORT_V18.md`.

## v1.8.4 Capacity Status

- 100 users: `not_run`
- 200 users: `not_run`
- 300 users: `not_run`
- 500 users: `not_run`
- Current maximum stable users: not established for v1.8.4.

Do not claim 500-user support unless the real 500-user Locust command passes and is recorded in `docs/V184_CAPACITY_VALIDATION.md`.

meizhaiseek v1.8 prepares the platform for a 500-user production profile.

Recommended production stack:

- PostgreSQL for APP data.
- Redis for cache, rate limit, RQ queue, and distributed run events.
- RQ workers split into general and video queues.
- SSE remains the realtime protocol; Redis Pub/Sub only wakes API instances.
- Shared artifact storage through `local_shared` or `s3`.

Local development remains:

- `APP_DB_BACKEND=sqlite`
- `TASK_QUEUE_BACKEND=inline`
- `EVENT_BACKEND=memory`
- `ARTIFACT_STORAGE_BACKEND=local`

No 500-user result is claimed unless `docs/CAPACITY_REPORT_V18.md` records an actual Locust run.
