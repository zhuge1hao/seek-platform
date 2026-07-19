# v1.8.8 200 User Capacity Gate

Version: `meizhaiseek v1.8.8`
Model: `meizhaiseek 2.0`

## Status

- 100-user v1.8.8 regression: `not_run`.
- 200-user v1.8.8 capacity gate: `not_run`.
- Current maximum stable users remains `100` from v1.8.7 until this branch passes a real 200-user run.
- 300/500-user tests are out of scope for v1.8.8 and must remain `not_run`.
- Blocking prerequisites on 2026-07-19: real video success/download matrix `not_run`, multi-instance SSE `not_run`, Docker daemon unavailable, and pip-audit gate `failed` due new `torch` advisory.

## Commands

```powershell
locust -f load_tests/locustfile.py --headless -u 100 -r 10 -t 15m --host http://127.0.0.1
locust -f load_tests/locustfile.py --headless -u 200 -r 20 -t 10m --host http://127.0.0.1
python apps/api/scripts/export_pool_metrics.py --metrics-url http://127.0.0.1/metrics
```

Run 200 users only after browser matrix, multi-instance SSE, pool metrics, Docker health, and quality gates pass.
