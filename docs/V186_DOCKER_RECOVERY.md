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

- Docker daemon: `not_run` in this document until P0 commands are executed on v1.8.6.
- VHDX SymbolicLink check: `not_run` in this document until P0 commands are executed on v1.8.6.
- Compose stack: `not_run`.
- Health endpoints: `not_run`.
- Runtime health: `not_run`.

## Evidence Log

P0 evidence will record:

- `docker version`
- `docker info`
- `docker context show`
- `wsl -l -v`
- VHDX link and target metadata
- `docker compose -f docker-compose.prod.yml config`
- `docker compose -f docker-compose.prod.yml up -d --build`
- `docker compose -f docker-compose.prod.yml ps`
- `/health`, `/health/live`, `/health/ready`, `/metrics`
- authenticated `/api/admin/runtime/health`

## Current Result

`not_run`
