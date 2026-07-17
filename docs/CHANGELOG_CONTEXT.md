# Changelog Context

## v1.8.5 - Business Queue And Storage Validation Cycle Started

Date: 2026-07-17

Branch: `stabilization/v1.8.5`

Planned focus:

- Dataset/Knowledge/Blueprint business queue closure.
- MinIO permission, TTL, streaming, and artifact download acceptance.
- pgvector non-empty migration, resume, idempotency, and top-k comparison.
- Browser `/agent` Run-card and conversation refresh smoke.
- Runtime health marker closeout for only real executed gates.

Out of scope:

- No new business agents.
- No v1.9 upgrade.
- No local video Agent refactor or Prompt change.
- No 200/300/500-user capacity tests.

## v1.8.4 - Validation Cycle Started

Date: 2026-07-16

Branch: `stabilization/v1.8.4`

Done at cycle start:

- v1.8.3 `/agent` frontend run-card/conversation refresh fix was committed on `stabilization/v1.8.3`.
- Runtime health and visible UI version were updated to `meizhaiseek v1.8.4`.
- Runtime validation markers now expose v1.8.4 P0-P4 gates as `not_run`, `failed`, or `passed`.

Not yet executed at cycle start:

- Full 8001-available video breakdown E2E.
- Worker crash/restart, zombie recovery, 50 video jobs, Redis pause/recovery.
- Dataset/Knowledge/Blueprint queue closure and pgvector non-empty migration resume.
- MinIO permission/TTL/streaming, backup recovery, Docker runtime final acceptance.
- 100/200/300/500-user capacity validation.

## Current Dirty Work After v1.8.3

Date: 2026-07-16

Not committed:

- `apps/web/src/app/agent/page.tsx`: added `conversationIdsRef` to avoid stale conversation-list closure when a new run reports a conversation ID not yet in local state.
- `apps/api/tests/test_agent_runs_api.py`: forces SQLite and explicit test admin password so tests do not read local production `.env`.
- `docker-compose.prod.yml`: forwards `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, and `DEEPSEEK_MODEL` into API and worker containers from `.env`.
- `AGENTS.md`, `docs/CODEX_HANDOFF.md`, `docs/NEXT_TASKS.md`, `docs/CHANGELOG_CONTEXT.md`: refreshed handoff package.
- `.env` was updated with local DeepSeek secret config outside git tracking. Never print or commit it.
- `ARCHITECTURE_EVALUATION_REPORT.md` remains protected dirty user work. Do not modify it.

Checks actually run after the `/agent` and test setup edits:

- `npm.cmd run build` passed.
- `python -m compileall apps/api` passed.
- `python -m unittest discover -s apps/api/tests` passed: 71 tests.
- `python -m pytest apps/api/tests` passed: 71 passed, 2 skipped.
- `.venv\Scripts\python.exe -m ruff check apps/api` passed.
- `.venv\Scripts\python.exe -m mypy apps/api` passed.
- `git diff --check` on touched functional files passed.

Operational notes:

- Production compose was started on 2026-07-15 with `worker-general=4`, `worker-video=2`.
- Admin password was reset during troubleshooting; do not record passwords in docs.
- DeepSeek was verified configured inside the API container on 2026-07-15 and `/health/ready` returned `ok`.
- During the 2026-07-16 handoff turn, Docker was not running and `http://127.0.0.1:8000/health/ready` was unavailable, so live health was not reverified.

## v1.8.3 - Full Type Gate, Queue Proof, pgvector Validation

Date: 2026-07-12

Branch: `stabilization/v1.8.3`

Commits:

- `26eb794cb6ae90ae38e2c71b6e12697f3acda4df` - `fix: close v1.8.3 type and queue P0 gaps`
- `d83603213ed34fc315d783a98aa1c51467f288f3` - `test: complete v1.8.3 queue and pgvector validation`

Done:

- Created v1.8.3 from v1.8.2 base `51913b4f8eb5e34e9fb170c4fe524c71ae28c6f4`.
- Updated backend runtime health and frontend visible version to `meizhaiseek v1.8.3`.
- Revalidated full `mypy apps/api`.
- Added/extended PostgreSQL pool edge coverage and Dataset clean queue coverage.
- Confirmed QA/Knowledge and Blueprint queue entry unit proof.
- Reviewed transformers vulnerability exceptions; raw pip-audit still fails, exact exception gate passes.
- Ran BGE-small-zh smoke: model loaded, dimension 512.
- Ran isolated pgvector non-empty migration: 5 docs, 60 chunks, dry-run/execute/verify/resume/top-k passed.
- Ran 100-user 15-minute Locust rerun: 0 failures, aggregate p95 110ms, submit p95 370ms.
- Confirmed Docker topology running healthy with PostgreSQL, Redis, MinIO, API, Web, Nginx, worker-general x4, worker-video x1.

Not done:

- P2 Redis pause/recovery full acceptance.
- P2 worker crash/restart/zombie recovery.
- P2 50 video jobs.
- P2 full MinIO permission/TTL/streaming.
- P3 200/300/500 user tests.

Accepted risk:

- `transformers 4.57.6` has three exact documented advisories accepted only for the local BGE embedding path.
- No standalone dataset/knowledge/blueprint workers; `worker-general` owns those queues.
- Dataset export queue is not accepted because no public API endpoint exists.

## v1.8.2 - Docker Recovery And Production Foundation

Done:

- Restored Docker Desktop Linux Engine without destructive WSL/Docker operations.
- Verified Docker VHDX symlink to `E:\USE\Docker\docker-desktop-disk\docker_data.vhdx`.
- Rebuilt production compose and started PostgreSQL, Redis, MinIO, API, Web, Nginx, worker-general, worker-video.
- Ran Alembic to `20260705_v18_initial`.
- Restored APP data from host SQLite into PostgreSQL and verified migration.
- Enabled pgvector and validated zero-source migration path.
- Improved type gate, Redis reuse, queue routing, cache safety, and SSE backoff.

Not done:

- Full P2 and P3 validation.

## v1.8 / v1.8.1 - Production Architecture And Hardening

Done:

- Added PostgreSQL/Alembic schema and SQLite-to-PostgreSQL migration.
- Added Redis cache/rate limit/events, RQ queue facade, workers.
- Added artifact storage facade and RAG provider facade.
- Added `/health/live`, `/health/ready`, `/metrics`, runtime health.
- Hardened JWT/admin password/table count/CLI connector/secret handling.
- Split queues into `general`, `video`, `dataset`, `knowledge`, `blueprint`.
- Optimized `/api/agents`, login rate limit, and Agent Run submit.

Not done:

- Full distributed failure acceptance.
- 500-user capacity proof.

## v1.7.x - Blueprint Stabilization

Done:

- Blueprint draft/version/test/release gate/publish/rollback/import/export/diff/history.
- Published video breakdown blueprint seed.
- Event hub and SSE/polling foundations.

## v1.6.x - Video Breakdown Productionization

Done:

- Real local Agent execution for video/script breakdown.
- Failed state when 8001 unavailable.
- Artifact, debug payload, result, and SSE/polling lifecycle.

## v1.5.x And Earlier - Core Product Base

Done:

- Auth, roles, user isolation.
- Admin, audit, Connector, Payload Preview, Debug Replay.
- Dataset, field mapping, clean/export, secure downloads.
- QA/RAG, knowledge base, DeepSeek streaming QA.
- APP SQLite migration and APP/RAG SQLite separation.

## Next Window Note

Top priority is `/agent` real user loop, not infra broadening: submit -> persisted conversation -> route restore -> real run -> status/result/error chat writeback.
