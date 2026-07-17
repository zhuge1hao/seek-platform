# v1.8.6 Docker Recovery

Version: `meizhaiseek v1.8.6`

Date: 2026-07-17

## Scope

P0 restores Docker Desktop Linux Engine without destructive Docker, WSL, Git, database, MinIO, or VHDX operations.

## Protected Data

- `E:\USE\Docker\docker-desktop-disk\docker_data.vhdx` must not be deleted, reformatted, pruned, or replaced.
- `C:\Users\Administrator\AppData\Local\Docker\wsl\disk\docker_data.vhdx` must remain a SymbolicLink or ReparsePoint to the E: drive target when present.
- `ARCHITECTURE_EVALUATION_REPORT.md` remains protected dirty user work and is not staged.

## Initial Status

- Docker daemon before recovery: `failed`, Docker client could not connect to `npipe:////./pipe/dockerDesktopLinuxEngine`.
- `com.docker.service` before recovery: `Stopped`.
- WSL before recovery: `Ubuntu` stopped, `docker-desktop` stopped.
- Local dev API/Web on ports `8000` and `3000` were stopped before compose startup to avoid port conflicts.

## Evidence Log

Executed on 2026-07-17:

- `docker version`: `passed`, client/server `29.4.0`, Docker Desktop `4.70.0`.
- `docker info`: `passed`, Linux engine ready, 12 CPUs, 15.54 GiB memory.
- `docker context show`: `desktop-linux`.
- `wsl -l -v`: `Ubuntu` running, `docker-desktop` running.
- VHDX link: `C:\Users\Administrator\AppData\Local\Docker\wsl\disk\docker_data.vhdx` is a `SymbolicLink` / `ReparsePoint` to `E:\USE\Docker\docker-desktop-disk\docker_data.vhdx`.
- VHDX target: exists, size `60353937408` bytes.
- `docker compose -f docker-compose.prod.yml config`: `passed`; raw output expanded local secrets and was not copied into this document.
- `docker compose -f docker-compose.prod.yml up -d --build`: `passed`.
- `docker compose -f docker-compose.prod.yml up -d --scale worker-general=4 --scale worker-video=2`: `passed`.
- `docker compose -f docker-compose.prod.yml ps`: `passed`.

Services after recovery:

- PostgreSQL: `healthy`.
- Redis: `healthy`.
- MinIO: `healthy`.
- API: `healthy`.
- Web: `healthy`.
- Nginx: `running`.
- `worker-general`: 4 containers running.
- `worker-video`: 2 containers running.

Health checks:

- `GET /health`: HTTP 200, `status=ok`.
- `GET /health/live`: HTTP 200, `status=ok`.
- `GET /health/ready`: HTTP 200, `status=ok`, `database.backend=postgres`, `redis.status=ok`, `queue.backend=redis`, `artifact_storage.backend=s3`, `rag.backend=pgvector`.
- `GET /metrics`: HTTP 200, Prometheus metrics returned.
- authenticated `GET /api/admin/runtime/health`: HTTP 200, `version=v1.8.6`, `model=meizhaiseek 2.0`, all unexecuted v1.8.6 acceptance markers remained `not_run`.

## Current Result

`passed`
