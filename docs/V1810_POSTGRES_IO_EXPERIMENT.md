# v1.8.10 PostgreSQL IO Experiment

Status: passed on 2026-07-31.

Compare synchronous_commit on/off using test-only session or override settings, then restore on. Compare API workers 1/2/4 while keeping total possible pool connections below PostgreSQL max_connections with operating reserve.

Baseline settings were synchronous_commit=on, fsync=on, full_page_writes=on, wal_sync_method=fdatasync, commit_delay=0, commit_siblings=5, and max_connections=100.

- workers=1, synchronous_commit=on, pool 20+20: submit p95 604ms.
- workers=1, synchronous_commit=off, pool 20+20: submit p95 633ms; no benefit, rejected.
- workers=2, synchronous_commit=on, pool 20+20 per process: submit p95 270ms.
- workers=4, synchronous_commit=on, pool 10+10 per process: submit p95 311ms.

Final selection is workers=2 with pool 20+20 per process, theoretical maximum 80 connections. synchronous_commit was restored to on.
