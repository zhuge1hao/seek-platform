# v1.8.10 200-User Results

Status: passed on round 1 on 2026-07-31.

Run 200 users for 15 minutes only after the v1.8.10 100-user gate passes. Submit p95 must be at most 1000ms. Up to three evidence-driven rounds are allowed; 300/500 users remain out of scope.

Round 1 completed 145,700 requests with 0 failures. Aggregate p50/p95/p99 was 14/82/650ms. Submit p50/p95/p99 was 42/110/190ms; `/api/agents` p95 was 35ms; login p95 was 390ms; conversations p95 was 59ms.

Pool wait p50/p95/p99 was 0.50/0.95/0.99ms, timeout 0, max in-use 9, overflow 0, waiters 0. Commit p95 was 8.86ms and execute p95 was 9.96ms. The observed queue peak was 186; after load stopped it drained from 117 to 0 in 31 seconds. API, Web, PostgreSQL, and Redis restart counts were 0.

Host: Intel Core i5-12400F, 6 cores/12 logical processors, 31.8GiB physical memory. Docker reported a 15.54GiB memory ceiling. Final topology used API workers 2, worker-general 4, worker-video 2, pool 20+20 per API process, and PostgreSQL max_connections 100. Redis used 12.91MiB and MinIO data used 1.1GiB after the run.

Compared with the v1.8.9 final submit p95 of 1800ms, v1.8.10 reached 110ms, a 93.9% reduction. Current maximum stable users: 200. No 300/500-user test was executed.
