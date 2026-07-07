# Docker Production

v1.8 production compose targets PostgreSQL + Redis + API + workers + Web + nginx. The local development path still uses SQLite, inline queue, memory events, and local artifacts.

Production compose uses:

- PostgreSQL for APP data when `APP_DB_BACKEND=postgres`.
- Redis for cache, rate limit, RQ queue, and distributed Agent Run events.
- API on port 8000 with `/health/ready` healthcheck.
- `worker-general` and `worker-video` RQ workers.
- Web on port 3000 with `npm run start`.
- nginx on port 80.
- Persistent `apps/api/runtime` and `apps/api/uploads` mounts.
- `host.docker.internal:8001` for the optional local video Agent connector.

API startup runs `alembic upgrade head` before Uvicorn when `APP_DB_BACKEND=postgres`; if migration fails, the API should not report ready.

Validate with `docker compose -f docker-compose.prod.yml config`. Build or start with Docker only when the daemon is available; do not record build/up/health as successful unless the command actually succeeds.
