# Observability

v1.8 adds:

- `X-Request-ID` on responses.
- Structured request timing through middleware.
- Optional `/metrics` endpoint when `prometheus-client` is installed.
- Runtime health component status for database, Redis, queue, events, artifact storage, RAG, and capacity profile.

Metrics should cover HTTP, DB pool, Redis, queue, worker, SSE, DeepSeek, 8001, and artifact paths as they are wired into production.

Secrets, connection strings, raw prompts, raw responses, and full workflow options must not be returned from health or metrics endpoints.

## v1.8.9 PostgreSQL Pool Metrics

- Live `/metrics` validation: `passed` on 2026-07-19.
- Exported metrics: `app_db_pool_acquire_seconds`, `app_db_pool_in_use`, `app_db_pool_idle`, `app_db_pool_overflow`, `app_db_pool_waiters`, `app_db_pool_timeout_total`, `app_db_pool_discarded_total`, `app_db_pool_reconnect_total`.
- Window exporter: `apps/api/scripts/export_pool_metrics.py` supports `--metrics-url`, `--window-seconds`, `--json-report`, and `--output`.
- Histogram quantiles are estimated from Prometheus buckets; the exporter does not use `sum/count` as a p95 substitute.
- 20 second live stress result: p50 `0.000543435s`, p95 `0.182753950s`, p99 `0.797634409s`, timeout count `0`, max in-use `10`, max overflow `5`, max waiters `29`.
- Post-stress gauges recovered to `in_use=0`, `overflow=0`, `waiters=0`.
