# v1.8.7 100 User Baseline

## Status

- Executed: `passed`
- Passed: `passed`
- Failed: `none`

## Command

```powershell
locust -f load_tests/locustfile.py --headless -u 100 -r 10 -t 15m --host http://127.0.0.1
```

## Results

Executed on 2026-07-17 against the Docker production stack.

Setup:

- Temporary operator users: `120`, generated with prefix `locust_v187_<random>_`.
- Password was passed only through environment variables and was not committed.
- `LOCUST_AGENT_TYPE=blue_ocean`.
- No real video workload was included.
- Initial `/health/ready`: `ok`, queue depths `0`.

Final Locust summary:

| Metric | Result | Gate |
| --- | ---: | --- |
| Users | 100 | executed |
| Duration | 15 minutes | executed |
| Total requests | 85,784 | executed |
| Failures | 0 / 0.00% | `<1%` passed |
| Aggregate p95 | 140 ms | `<=500 ms` passed |
| Aggregate p99 | 310 ms | `<=1000 ms` passed |
| `/api/agents` p95 | 79 ms | `<=300 ms` passed |
| Login p95 | 230 ms | `<=500 ms` passed |
| Agent submit p95 | 480 ms | `<=500 ms` passed |
| Max response time | 907 ms | recorded |

Endpoint summary:

| Endpoint | Requests | Failures | Avg | p95 | p99 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `POST /api/agent-runs` | 4,154 | 0 | 221 ms | 480 ms | 630 ms |
| `GET /api/agent-runs/:id/events` | 2,070 | 0 | 31 ms | 92 ms | 140 ms |
| `GET /api/agent-runs/:id/summary` | 2,078 | 0 | 33 ms | 94 ms | 150 ms |
| `GET /api/agents` | 24,407 | 0 | 27 ms | 79 ms | 120 ms |
| `POST /api/auth/login` | 100 | 0 | 154 ms | 230 ms | 250 ms |
| `GET /api/conversations` | 24,407 | 0 | 36 ms | 96 ms | 150 ms |
| `GET /api/qa/health` | 4,161 | 0 | 100 ms | 220 ms | 300 ms |
| `GET /health` | 24,407 | 0 | 12 ms | 32 ms | 57 ms |

Post-run checks:

- `/health/ready`: `ok`.
- Final queue depth: `0` for `general`, `video`, `dataset`, `knowledge`, and `blueprint`.
- API RSS: approximately `158 MB` after the run; no sustained growth was observed during the post-run check.
- Docker services remained running/healthy.

Limitations:

- Pool wait p95 was not separately exported by current metrics and is therefore `not_run`.
- 200/300/500-user tests remain `not_run` by v1.8.7 scope.

Outcome:

- `CAPACITY_LAST_VERIFIED_USERS=100`.
- `CAPACITY_LAST_TEST_PASSED=passed`.
- Current maximum stable user count: `100`.
