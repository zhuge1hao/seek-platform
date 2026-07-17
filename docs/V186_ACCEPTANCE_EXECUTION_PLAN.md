# v1.8.6 Acceptance Execution Plan

Version: `meizhaiseek v1.8.6`

Date: 2026-07-17

## Scope

Execute the v1.8.5 acceptance scripts with real Docker PostgreSQL, Redis/RQ, MinIO/S3, pgvector, and browser evidence after Docker recovers.

## Items

| Area | Script or Check | Status |
| --- | --- | --- |
| Dataset queue | `python apps/api/scripts/acceptance_dataset_queue.py --json-report` | `not_run` |
| Knowledge queue | `python apps/api/scripts/acceptance_knowledge_queue.py --json-report` | `not_run` |
| Blueprint queue | `python apps/api/scripts/acceptance_blueprint_queue.py --json-report` | `not_run` |
| MinIO storage | `python apps/api/scripts/acceptance_minio_storage.py --json-report --size 10MB` | `not_run` |
| pgvector migration | `python apps/api/scripts/acceptance_pgvector_nonempty.py --json-report` | `not_run` |
| Browser Agent smoke | real browser or Playwright smoke | `not_run` |

## Execution Update - 2026-07-17

- Dataset queue: `passed`.
- Knowledge queue: `failed`.
- Blueprint queue: `passed`.
- MinIO storage: `partial`; signed-url/download/secret-leak passed, TTL/streaming/user-isolation not run.
- pgvector migration: `passed` for dry-run/execute/verify/repeat verify in Docker network; resume/top-k not run.
- Browser Agent smoke: `not_run`.

## Rules

- Docker-dependent acceptance stays `not_run` if Docker is unavailable.
- Failed scripts are recorded as `failed`; no partial result is upgraded to `passed`.
- Runtime health markers are changed to `passed` only after command evidence exists.
- No runtime data, logs, uploads, local videos, video output, Docker data, or MinIO data are committed.

## Current Result

`not_run`
