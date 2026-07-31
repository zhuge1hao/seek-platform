# v1.8.10 100-User Results

Status: passed on the first valid performance round on 2026-07-31.

Run 100 users for 15 minutes only after quality, browser, Docker, queue, and transaction-budget gates pass. Record request, endpoint, database, pool, queue, resource, and restart evidence.

The valid round completed 90,106 requests with 0 failures. Aggregate p50/p95/p99 was 12/45/84ms. Submit p50/p95/p99 was 34/95/140ms; `/api/agents` p95 was 28ms; login p95 was 210ms. Pool wait p50/p95/p99 was 0.50/0.95/0.99ms, timeout 0, max in-use 6, overflow 0, waiters 0. Final queue depth was 0 and API/Web restart count was 0.

Two environment-preparation attempts were rejected before the valid round: missing accounts produced login 401, then viewer accounts correctly produced submit 403. Both were diagnosed and corrected; neither is included in performance results.
