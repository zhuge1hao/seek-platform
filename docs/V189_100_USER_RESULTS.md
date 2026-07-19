# v1.8.9 100-user Results

Version: `meizhaiseek v1.8.9`

## Status

- Execution rounds: `2`.
- Final result: `passed`.
- Error rate: `0.00%`.
- Aggregate p95: `140 ms`.
- Aggregate p99: `300 ms`.
- Submit p95: `470 ms`.
- Pool-wait p95: `0.000952704 s`.
- Final queued: `0`.
- Final executing: `0`.

## Gate

The 100-user regression passed on round 2, so the 200-user gate is unblocked.

## Round 1

- Result: `failed`.
- Command: `locust -f load_tests/locustfile.py --headless -u 100 -r 10 -t 15m --host http://127.0.0.1`.
- Temporary users: `300`, prefix `loadtest_v189_100_20260719180752_`; password was held only in process environment and was not committed.
- Total requests: `86,102`.
- Failures: `0`.
- Error rate: `0.00%`.
- Aggregate p50/p95/p99: `20 ms` / `160 ms` / `400 ms`.
- `/api/agents` p95: `100 ms`.
- Login p95: `340 ms`.
- Submit p95: `590 ms`.
- Pool-wait p50/p95/p99: `0.000527914 s` / `0.003845081 s` / `0.028871897 s`.
- Pool timeout count: `0`.
- Max pool in-use / overflow / waiters: `10` / `5` / `11`.
- Final queue depth: `general=0`, `video=0`, `dataset=0`, `knowledge=0`, `blueprint=0`.

Failure reason:

- The run failed the v1.8.9 100-user submit latency gate because `/api/agent-runs` p95 was `590 ms`, above the `500 ms` limit.

Remediation before retry:

- Applied non-secret v1.8.9 override settings: `APP_DB_POOL_SIZE=10`, `APP_DB_MAX_OVERFLOW=10`, and `AGENT_RUN_SUBMIT_TIMING=false`.
- Recreated the production API with the override and verified `/health/ready` reported `pool_size=10`, `max_overflow=10`, `max_total=20`, `in_use=0`, `idle=1`, `waiters=0`, and `timeout_total=0`.

## Round 2

- Result: `passed`.
- Command: `locust -f load_tests/locustfile.py --headless -u 100 -r 10 -t 15m --host http://127.0.0.1`.
- Temporary users: `300`, prefix `loadtest_v189_100r2_20260719182512_`; password was held only in process environment and was not committed.
- Total requests: `84,808`.
- Failures: `0`.
- Error rate: `0.00%`.
- Aggregate p50/p95/p99: `19 ms` / `140 ms` / `300 ms`.
- Max response time: approximately `1008 ms`.
- `/api/agents` p95/p99: `69 ms` / `130 ms`.
- Login p95/p99: `260 ms` / `280 ms`.
- Submit p95/p99: `470 ms` / `660 ms`.
- `/api/conversations` p95: `85 ms`.
- `/api/qa/health` p95: `200 ms`.
- `/api/agent-runs/:id/events` p95: `73 ms`.
- `/api/agent-runs/:id/summary` p95: `78 ms`.
- Pool-wait p50/p95/p99: `0.000501423 s` / `0.000952704 s` / `0.000992818 s`.
- Pool timeout count: `0`.
- Max pool in-use / idle / overflow / waiters: `15` / `10` / `9` / `0`.
- Final `/health/ready` queue depth: `general=0`, `video=0`, `dataset=0`, `knowledge=0`, `blueprint=0`.
- Container restart counts after the run: `0` for API, web, nginx, PostgreSQL, Redis, MinIO, four general workers, and two video workers.

Evidence files were written under `apps/api/runtime/logs/` and are intentionally not committed.
