# v1.8.8 PostgreSQL Pool Observability

Version: `meizhaiseek v1.8.8`
Model: `meizhaiseek 2.0`

## Coded Metrics

- `app_db_pool_acquire_seconds`
- `app_db_pool_in_use`
- `app_db_pool_idle`
- `app_db_pool_overflow`
- `app_db_pool_waiters`
- `app_db_pool_timeout_total`
- `app_db_pool_discarded_total`
- `app_db_pool_reconnect_total`

## Status

- Metrics are coded and covered by unit tests.
- `metrics.render_metrics()` confirmed all pool metric names are registered and the rendered text did not include `secret`, `password`, or `api_key`.
- Runtime health exposes non-sensitive PostgreSQL pool summary under `database.pool` plus compatible `database.pool_size`.
- Production pool-wait p50/p95/p99 remains `not_run` until collected from `/metrics` after Locust.

## Export Command

```powershell
python apps/api/scripts/export_pool_metrics.py --metrics-url http://127.0.0.1/metrics
```
