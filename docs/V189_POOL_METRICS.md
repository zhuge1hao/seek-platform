# v1.8.9 Pool Metrics

Version: `meizhaiseek v1.8.9`

## Live Metrics

- Metrics endpoint: `passed`; `Invoke-WebRequest http://127.0.0.1:8000/metrics` returned HTTP `200`, length `12795`.
- Secret scan: `passed`; the metrics response did not contain DSNs, passwords, S3 secret names, or complete SQL text.
- `app_db_pool_acquire_seconds`: `passed`.
- `app_db_pool_in_use`: `passed`.
- `app_db_pool_idle`: `passed`.
- `app_db_pool_overflow`: `passed`.
- `app_db_pool_waiters`: `passed`.
- `app_db_pool_timeout_total`: `passed`.
- `app_db_pool_discarded_total`: `passed`.
- `app_db_pool_reconnect_total`: `passed`.

## Capacity Values

- Live stress command: 40 local threads hit `/health/ready` while collecting `/metrics` for a 20 second window.
- Stress requests: `815`; HTTP/server errors: `0`.
- pool-wait p50: `0.000543435s`.
- pool-wait p95: `0.182753950s`.
- pool-wait p99: `0.797634409s`.
- pool timeout count: `0`.
- max in-use: `10`.
- max idle: `2`.
- max overflow: `5`.
- max waiters: `29`.
- discarded count during window: `0`.
- reconnect count during window: `0`.
- Post-stress gauge recovery: `passed`; after 5 seconds `in_use=0`, `idle=5`, `overflow=0`, `waiters=0`.
- Exporter CLI: `passed`; `python apps/api/scripts/export_pool_metrics.py --metrics-url http://127.0.0.1:8000/metrics --json-report --window-seconds 2 --output apps/api/runtime/logs/pool_metrics_v189_cli.json`.

## Boundaries

- A live timeout was not forced in the production stack because the stress run returned `pool_timeout_total=0`. Timeout counter behavior remains covered by `apps/api/tests/test_app_sqlite.py`.
- Runtime log JSON files under `apps/api/runtime/logs/` are evidence artifacts and are not committed.
