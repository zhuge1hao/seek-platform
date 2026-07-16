# Scalability 500 Users

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
