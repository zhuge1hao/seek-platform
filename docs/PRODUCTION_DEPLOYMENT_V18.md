# Production Deployment v1.8

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
