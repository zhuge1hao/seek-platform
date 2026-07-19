# v1.8.8 Multi-instance SSE

Version: `meizhaiseek v1.8.8`
Model: `meizhaiseek 2.0`

## Status

- Acceptance script updated for v1.8.8 naming and still requires live production topology.
- Production execution: `not_run`; Docker daemon was unavailable on 2026-07-19.
- Marker remains `not_run` until the current branch is validated with two API instances sharing PostgreSQL, Redis, JWT secret, artifact backend, and RAG backend.

## Command

```powershell
python apps/api/scripts/acceptance_redis_recovery.py --api-a http://127.0.0.1:8000 --api-b-port 8002 --json-report
```

## Required Evidence

- API A creates run; API B receives SSE through Redis-backed event bus.
- Redis pause/recovery preserves DB-backed summary fallback and new post-recovery events.
- One terminal event, one assistant message per run, no sensitive fields in SSE payload.
