# meizhaiseek v1.8.1 Performance Optimization

Date: 2026-07-06

## Changes

- Added a small psycopg connection pool to the backend-aware app DB adapter to avoid one PostgreSQL connection per store call.
- Set production compose API pool defaults to `APP_DB_POOL_SIZE=5` and `APP_DB_MAX_OVERFLOW=5`.
- Optimized `/api/agents` to use light summaries, batched blueprint lookups, and short TTL cache. The list path no longer performs local Agent 8001 health checks.
- Reduced Agent Run submit work to validation, minimal DB writes, queue enqueue, and response. Successful audit logging is deferred to background tasks.
- Redis login rate limit now uses a pipeline for IP and username counters.
- Split RQ queues into `general`, `video`, `dataset`, `knowledge`, and `blueprint`; compose now runs `worker-general=4` and `worker-video=2`.

## Verified Capacity

Before v1.8.1:

- 100 users: aggregate p95 about 5400 ms.
- `/api/agents`: p95 about 8100 ms.
- Agent Run submit: p95 about 7800 ms.
- Login: p95 about 2000 ms.

After v1.8.1:

- 20 users, 2 minutes: 2469 requests, 0 failures, aggregate p95 44 ms, `/api/agents` p95 19 ms, login p95 110 ms, submit p95 120 ms.
- 100 users, 2 minutes: 11399 requests, 0 failures, aggregate p95 140 ms, `/api/agents` p95 87 ms, login p95 300 ms, submit p95 490 ms.
- 100 users, 10 minutes: 57473 requests, 0 failures, aggregate p95 140 ms, p99 310 ms, `/api/agents` p95 87 ms, login p95 330 ms, submit p95 520 ms.

## Gate Result

- P1 minimum gate passed: error rate 0%, aggregate p95 under 1000 ms, `/api/agents` under 1000 ms, login under 1000 ms, submit under 1000 ms.
- Priority target for submit p95 under 500 ms was narrowly missed in the 10 minute run: observed p95 520 ms.

## Not Executed

- 200/300/500 user tests were not executed in this turn because P2 distributed acceptance remains incomplete.
