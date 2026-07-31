# v1.8.10 Database Commit Observability

Status: passed on the live production `/metrics` endpoint.

Metrics cover fixed-label execute operations, commit/rollback latency and counts, commit failures, submit stages, and per-submit transaction/commit counts. SQL, table names, identifiers, paths, prompts, DSNs, and credentials are not labels.

During a 100-request/concurrency-20 window: execute p50/p95/p99 was 9.33/24.30/42.18ms; commit was 7.09/22.29/24.70ms; rollback was 5.47/18.96/23.79ms; pool wait was 0.51/0.97/92.00ms. Pool timeout was 0, max in-use 12, max overflow 14, and max waiters 0. Final gauges returned to in-use 0, overflow 0, waiters 0.
