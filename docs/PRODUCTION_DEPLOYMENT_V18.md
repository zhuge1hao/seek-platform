# Production Deployment v1.8

## v1.8.4 Validation Note - 2026-07-16

Runtime target: `meizhaiseek v1.8.4`, model display `meizhaiseek 2.0`.

Required production runtime health for final acceptance:

- `database.backend=postgres`
- `redis.status=ok`
- `queue.backend=redis`
- `artifact_storage.backend=s3`
- `rag.backend=pgvector`
- no secrets in responses

Current v1.8.4 production Docker, MinIO, pgvector, and capacity gates remain `not_run` until the commands in the v1.8.4 acceptance docs are executed.

## v1.8.2 Docker Recovery Note - 2026-07-07

The local production compose was recovered and started after Docker Desktop Linux Engine was unavailable.

Verified running services:

- PostgreSQL with pgvector, healthy.
- Redis, healthy.
- MinIO, healthy; artifact bucket initialized.
- API, healthy.
- Web, healthy.
- Nginx, running on `http://127.0.0.1`.
- `worker-general`, running.
- `worker-video`, running.

Data restore:

- Alembic current: `20260705_v18_initial (head)`.
- Host APP SQLite was backed up under runtime and migrated into PostgreSQL.
- Migration verify passed.
- RAG pgvector migration ran with zero source documents/chunks.

Readiness warning:

- The local admin password was restored to the legacy default at user request.
- `/health/ready` is degraded while that password remains active.
- Do not use this state as a production-ready security posture.

Recommended compose path:

```powershell
docker compose -f docker-compose.prod.yml config
docker compose -f docker-compose.prod.yml up --build -d
```

Production env essentials:

```text
APP_DB_BACKEND=postgres
APP_DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://redis:6379/0
CACHE_BACKEND=redis
EVENT_BACKEND=redis
TASK_QUEUE_BACKEND=redis
ARTIFACT_STORAGE_BACKEND=local_shared
RAG_BACKEND=sqlite
AUTH_TOKEN_SECRET=...
MEIZHAISEEK_ADMIN_INITIAL_PASSWORD=...
```

API startup runs Alembic before Uvicorn in the production compose. `/health/live` checks process liveness. `/health/ready` checks deployment readiness.
