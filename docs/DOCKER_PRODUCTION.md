# Docker Production

v1.7.2 changes Web production Docker to a dependencies/builder/runner multi-stage image.

Production compose uses:

- API on port 8000 with `/health` healthcheck.
- Web on port 3000 with `npm run start`.
- Persistent `apps/api/runtime` and `apps/api/uploads` mounts.
- `host.docker.internal:8001` for the optional local video Agent connector.
- No database container; APP SQLite and RAG SQLite remain separate files.

Validate with `docker compose -f docker-compose.prod.yml config`. Build with `docker compose -f docker-compose.prod.yml build` only when Docker is available.
