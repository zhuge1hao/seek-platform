# v1.8.10 Submit Profile Baseline

Status: passed on 2026-07-31.

The detached v1.8.9 baseline commit `0ae8e5a` produced 16 transactions and 16 commits for one successful SQLite TestClient submit. Historical v1.8.9 200-user submit p95 values were 1400ms, 2500ms, and 1800ms.

The rebuilt v1.8.10 PostgreSQL stack produced 4 transactions, 4 acquires, 8 executes, 1 commit, and 3 read-only rollbacks per successful request. Serial 20-request latency was p50 32.35ms, p95 86.65ms, p99 131.31ms. At 100 requests/concurrency 20 it was p50 435.20ms, p95 604.00ms, p99 648.49ms with zero failures.
