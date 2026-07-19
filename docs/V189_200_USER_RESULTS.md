# v1.8.9 200-user Results

Version: `meizhaiseek v1.8.9`

## Status

- Execution rounds: `3`.
- Final result: `failed`.
- Error rate: `0.00%` in the final round.
- Aggregate p95: `490 ms`.
- Aggregate p99: `920 ms`.
- Submit p95: `1800 ms`.
- Pool-wait p95: `0.000953807 s`.
- Final queued: `0`.
- Final executing: `0`.
- Current maximum stable users: `100`.

## Scope

300-user and 500-user tests are out of scope for v1.8.9 and remain `not_run`.

## Round 1

- Result: `failed`.
- Command: `locust -f load_tests/locustfile.py --headless -u 200 -r 20 -t 10m --host http://127.0.0.1`.
- Temporary users: `300`, prefix `loadtest_v189_200_20260719184519_`; password was held only in process environment and was not committed.
- Total requests: `74,194`.
- Failures: `20`; error rate `0.03%`.
- Aggregate p50/p95/p99: `40 ms` / `890 ms` / `2600 ms`.
- `/api/agents` p95: `230 ms`.
- Login p95: `880 ms`.
- Submit p95: `1400 ms`.
- Pool-wait p50/p95/p99: `0.000529414 s` / `0.013558287 s` / `0.073338011 s`.
- DB pool timeout count: `0`.
- Max pool in-use / overflow / waiters: `20` / `10` / `18`.
- Queue after run: `general=598` immediately after the test; workers drained it to `0` before retry.

Failure causes:

- The local single-IP login ramp triggered 20 HTTP 429 responses from the IP rate limiter.
- Aggregate p99 exceeded `2000 ms`.
- Submit p95 exceeded the `1000 ms` 200-user gate.

Remediation before round 2:

- Added `LOGIN_RATE_LIMIT_PER_WINDOW=120` to the non-secret v1.8.9 override for local shared-IP capacity tests.
- Changed the Locust SSE task to subscribe to the user's latest submitted run instead of creating a second hidden run, aligning the test mix with the intended controlled Agent/Blueprint share and reducing queue amplification.
- Rebuilt API and restored `worker-general=4`, `worker-video=2`.

## Round 2

- Result: `failed`.
- Total requests: `91,841`.
- Failures: `0`; error rate `0.00%`.
- Aggregate p50/p95/p99: `280 ms` / `670 ms` / `1900 ms`.
- `/api/agents` p95: `560 ms`.
- Login p95: `830 ms`.
- Submit p95: `2500 ms`.
- Pool-wait p50/p95/p99: `0.026618890 s` / `0.109555556 s` / `0.222453117 s`.
- DB pool timeout count: `0`.
- Max pool in-use / overflow / waiters: `20` / `10` / `20`.
- Queue after run: `general=0`, `video=0`, `dataset=0`, `knowledge=0`, `blueprint=0`.

Failure causes:

- Submit p95 exceeded the `1000 ms` gate.
- `/api/agents` p95 exceeded the `500 ms` gate.
- Login p95 exceeded the `800 ms` gate.

Remediation before round 3:

- Increased only the API-side PostgreSQL pool to `APP_DB_POOL_SIZE=20`, `APP_DB_MAX_OVERFLOW=20`.
- Verified PostgreSQL `max_connections=100`; current connections before the retry were below the new maximum connection envelope.
- Recreated API and verified `/health/ready` reported `pool_size=20`, `max_overflow=20`, `max_total=40`, and queue depth `0`.

## Round 3

- Result: `failed`.
- Total requests: `100,301`.
- Failures: `0`; error rate `0.00%`.
- Aggregate p50/p95/p99: `180 ms` / `490 ms` / `920 ms`.
- `/api/agents` p95: `390 ms`.
- Login p95: `670 ms`.
- Submit p95: `1800 ms`.
- `/api/agent-runs/:id/events` p95: `400 ms`.
- `/api/agent-runs/:id/summary` p95: `420 ms`.
- `/api/conversations` p95: `450 ms`.
- `/api/qa/health` p95: `590 ms`.
- Pool-wait p50/p95/p99: `0.000502003 s` / `0.000953807 s` / `0.000993967 s`.
- DB pool timeout count: `0`.
- Max pool in-use / idle / overflow / waiters: `25` / `20` / `20` / `0`.
- Final `/health/ready` queue depth: `general=0`, `video=0`, `dataset=0`, `knowledge=0`, `blueprint=0`.
- Container restart counts after the run: `0` for API, web, nginx, PostgreSQL, Redis, MinIO, four general workers, and two video workers.

Final gate conclusion:

- Error rate, aggregate p95, aggregate p99, `/api/agents` p95, login p95, pool-wait p95, DB timeout, queue drain, and container stability passed in round 3.
- Submit p95 remained `1800 ms`, above the `1000 ms` gate, after three reasonable tuning attempts.
- `CAPACITY_LAST_VERIFIED_USERS` remains `100`.
- `CAPACITY_LAST_TEST_PASSED` is `failed` for the latest 200-user gate.
