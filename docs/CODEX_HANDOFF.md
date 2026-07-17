# Codex Handoff

## v1.8.7 Active Handoff

- Branch: `stabilization/v1.8.7`
- Version: `meizhaiseek v1.8.7`
- Model display: `meizhaiseek 2.0`
- Protected dirty user work: `ARCHITECTURE_EVALUATION_REPORT.md`

Current goal: close v1.8.6 failed/not-run production evidence for Knowledge queue, MinIO permission/TTL/streaming, pgvector resume/top-k, browser `/agent` smoke, pip-audit risk recheck, and 100-user baseline rerun.

Current validation defaults: v1.8.4 video E2E, worker recovery, video queue 50, Redis recovery, v1.8.6 Dataset queue, Blueprint queue, pgvector dry-run/execute/verify, SQL guardrails, PostgresPool tests, and distributed service tests have real evidence. v1.8.7 Knowledge queue acceptance, MinIO full acceptance, pgvector resume/top-k, and browser core Run-card smoke have real evidence. Browser video/download/cancel/retry, pip-audit recheck, and v1.8.7 100-user baseline still need closure.

Knowledge acceptance evidence on 2026-07-17:

- Root cause: backend successful ingest status is `completed`, while v1.8.6 acceptance only accepted `ready`.
- Fix: acceptance accepts `ready` or `completed` with `chunk_count > 0`; SQLite RAG legacy schema allowlist is restored; Docker API and worker-general mount BGE model read-only.
- BGE worker smoke: `/app/models/bge-small-zh`, loadable, dimension `512`.
- `acceptance_knowledge_queue.py --json-report`: `passed`, 5 documents, 55 chunks, reindex `completed`, top-k retrieval `source_count=5`.

Browser core smoke evidence on 2026-07-17:

- Playwright/Chrome command: `npm.cmd run e2e:agent -- --project=chrome`.
- Result: `1 passed`.
- Run: `run_20260717094756_2c66e2b0`.
- Conversation: `conv_20260717094756_b1a833d3`.
- Covered: UI login, normal Agent Run submit, left conversation route refresh, Run-card display, reload restore, failed terminal state, and second-user isolation.
- Still not covered: video UI artifacts, cancel, retry, and browser SSE terminal-close timing; do not mark the full `BROWSER_AGENT_SMOKE_VERIFIED` marker `passed` from this partial smoke alone.

Execution note for 2026-07-17: do not commit `AGENTS.md`, current `docker-compose.prod.yml` local env pass-through, `.env`, runtime logs, model files, uploads, Docker data, MinIO data, or `ARCHITECTURE_EVALUATION_REPORT.md`.

## v1.8.7 Scope

- Do not add business agents.
- Do not upgrade to v1.9.
- Do not refactor local video Agent or modify its Prompt.
- Do not run 200/300/500-user capacity tests in v1.8.7; leave them for a later version.
- Do not modify or stage `ARCHITECTURE_EVALUATION_REPORT.md`.

## v1.8.4 P0 Video E2E Result - 2026-07-16

Passed:

- Production Docker stack used API + PostgreSQL + Redis/RQ + MinIO/S3 + `worker-video` x2.
- Local 8001 video Agent health returned `status=ok`; API container reached `http://host.docker.internal:8001/health`.
- Real video run `run_20260716094829_ecf1360b` completed.
- Conversation `conv_20260716094829_e4b8023b` was listed after submit.
- Queue job `agent-run-run_20260716094829_ecf1360b` was consumed by `worker-video`.
- DB counts for the successful run: `agent_runs=1`, `agent_conversations=1`, `agent_messages=2`, `artifacts=260`, `debug_payloads=1`.
- SSE emitted running/progress/completed events.
- Assistant message status was `completed`.
- Excel, JSON report, evidence image, and folder manifest downloads all returned HTTP 200 through S3 artifact route.
- `final_shots=45`, `data_columns=45`, `embedded_images=45`.

Failure path:

- Run `run_20260716093735_2b597cc0` failed when the Docker worker could not reach a loopback-only 8001 Connector URL.
- Conversation `conv_20260716093735_f215d04d` contains one user completed message and one assistant failed message.
- No duplicate assistant message was observed.

Fixes included:

- Docker workers now repair loopback video Connector URLs to `VIDEO_AGENT_BASE_URL` when set.
- Artifact resolution translates Windows host paths under `apps/api/runtime` to the mounted container path.
- Video result normalization handles Windows `video_file` stem/name correctly.
- S3 artifact downloads support non-ASCII filenames in `Content-Disposition`.

Still `not_run`:

- Direct browser `/agent` Run-card smoke.
- Direct browser left conversation refresh smoke.
- P1 worker recovery, 50 video jobs, Redis pause/recovery.
- P2 Dataset/Knowledge/Blueprint and pgvector non-empty migration.
- P3 full MinIO TTL/permission/streaming and backup recovery.
- P4 100/200/300/500-user capacity and deployment pipeline.

## Project

- Project: `meizhaiseek-platform`
- Local path: `E:\USE\codexhome\agents-cowork\meizhaiseek-platform`
- GitHub: `https://github.com/zhuge1hao/seek-platform.git`
- Branch: `stabilization/v1.8.3`
- HEAD at handoff: `d83603213ed34fc315d783a98aa1c51467f288f3`
- Version: `meizhaiseek v1.8.3`
- Model display: `meizhaiseek 2.0`
- Protected dirty user work: `ARCHITECTURE_EVALUATION_REPORT.md`

Do not modify, stage, or whitespace-fix `ARCHITECTURE_EVALUATION_REPORT.md`.

## Current Goal

Keep v1.8.3 stable while finishing the real `/agent` task/chat loop:

1. After a task is submitted in `/agent`, the left conversation list must add a real backend conversation and keep it after refresh.
2. Switching to another route and returning to `/agent` must restore the selected task/chat/run state.
3. Script/video breakdown must execute through the platform backend, queue/workflow, and local Agent, not create only UI state.
4. Run status/result/error must write back to the matching chat record.

No v1.9 work, no new business agent, no local video-Agent prompt rewrite.

## Tech Stack And Startup

- Frontend: Next.js App Router, React 18, TypeScript, Tailwind, SWR, lucide-react.
- Backend: FastAPI, Pydantic, sqlite3, psycopg, SQLAlchemy async, Alembic.
- Production: PostgreSQL/pgvector, Redis/RQ, Redis events, MinIO/S3, Prometheus metrics, Nginx.
- Local video Agent: `http://127.0.0.1:8001`.
- Docker-to-host video Agent: `http://host.docker.internal:8001`.

Dev all-in-one:

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

Backend only:

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\api
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend only:

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run dev -- -p 3000
```

Production compose:

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
docker compose -f docker-compose.prod.yml up -d --build --scale worker-general=4 --scale worker-video=2
docker compose -f docker-compose.prod.yml ps
```

## Key Directories

```text
apps/api/main.py              FastAPI app, health, metrics
apps/api/routers              HTTP routes
apps/api/services             stores, auth, Connector, Dataset, QA/RAG, Blueprint
apps/api/db                   PostgreSQL/Alembic/SQLAlchemy schema
apps/api/tasks                inline/RQ queue facade and task entry points
apps/api/workers              RQ worker entry
apps/api/storage              local/local_shared/S3 artifact providers
apps/api/rag                  SQLite/pgvector RAG providers
apps/api/scripts              smoke, migration, verification scripts
apps/api/tests                unittest/pytest coverage
apps/api/runtime              runtime data, never commit
apps/api/uploads              uploaded files, never commit
apps/web/src/app              pages and route UI
apps/web/src/components       Agent, Chat, Dataset, Admin, Blueprint UI
apps/web/src/hooks            SWR, SSE, polling hooks
apps/web/src/lib              API client, auth, query keys, registry
docs                          handoff, testing, capacity, architecture docs
load_tests                    Locust scripts
```

## Completed Version Record

### v1.8.3

- Branch `stabilization/v1.8.3` was created from v1.8.2 base `51913b4f8eb5e34e9fb170c4fe524c71ae28c6f4`.
- P0 commit pushed: `26eb794cb6ae90ae38e2c71b6e12697f3acda4df`.
- P1 commit pushed: `d83603213ed34fc315d783a98aa1c51467f288f3`.
- Runtime/frontend version is `meizhaiseek v1.8.3`; model remains `meizhaiseek 2.0`.
- P1 gates previously passed: compileall, ruff, mypy, unittest 71 OK, pytest 71 passed / 2 skipped, Bandit High=0 Medium=0.
- BGE-small-zh smoke passed with 512-dimensional embeddings.
- Isolated pgvector non-empty migration validation passed on 5 docs / 60 chunks.
- 100-user 15-minute Locust rerun passed: 0 failures, aggregate p95 110ms, submit p95 370ms.
- Docker production topology previously ran healthy with PostgreSQL, Redis, MinIO, API, Web, Nginx, `worker-general` x4, `worker-video` x1.
- Dataset export queue acceptance is not passed because no public Dataset export enqueue endpoint exists.
- P2/P3 remain not executed.

### v1.8.2

- Restored Docker Desktop Linux Engine without destructive WSL/Docker operations.
- Verified Docker VHDX symlink to `E:\USE\Docker\docker-desktop-disk\docker_data.vhdx`.
- Rebuilt production compose and started PostgreSQL, Redis, MinIO, API, Web, Nginx, worker-general, worker-video.
- Ran Alembic to `20260705_v18_initial`.
- Restored APP data from host SQLite into PostgreSQL and verified migration.
- Enabled pgvector and validated zero-source migration path.
- Improved type gate, Redis reuse, queue routing, cache safety, and SSE backoff.

### v1.8 / v1.8.1

- Added PostgreSQL/Alembic schema and SQLite-to-PostgreSQL migration.
- Added Redis cache/rate limit/events, RQ queue facade, workers.
- Added artifact storage facade and RAG provider facade.
- Added `/health/live`, `/health/ready`, `/metrics`, runtime health.
- Hardened JWT/admin password/table count/CLI connector/secret handling.
- Split queues into `general`, `video`, `dataset`, `knowledge`, `blueprint`.
- Optimized `/api/agents`, login rate limit, and Agent Run submit.

### v1.7.x

- Added Blueprint governance: draft/version/test/release gate/publish/rollback/import/export/diff/history.
- Published video breakdown blueprint seed.
- Added event hub and SSE/polling foundations.

### v1.6.x

- Productionized video breakdown: real local Agent execution, failed state when 8001 is unavailable, artifacts, debug payloads, result persistence, SSE/polling lifecycle.

### v1.5.x And Earlier

- Auth, roles, user isolation.
- Admin, audit, Connector, Payload Preview, Debug Replay.
- Dataset, field mapping, clean/export, secure downloads.
- QA/RAG, knowledge base, DeepSeek streaming QA.
- APP SQLite migration and APP/RAG SQLite separation.

## Current Problem

The main remaining product problem is `/agent` user-facing correctness:

- The platform has solid production infra, but `/agent` must still be proven end-to-end from submit -> persisted conversation -> real run -> status/result/error chat writeback -> route restore.
- A small frontend fix is currently dirty in `apps/web/src/app/agent/page.tsx`: it tracks known conversation IDs in a ref so run updates for a newly submitted conversation can trigger conversation refresh without stale React closure state.
- Backend persistence/writeback coverage exists and was strengthened in `apps/api/tests/test_agent_runs_api.py`.

## Latest Explicit User Request

Generate a new-window handoff package only. Do not continue feature work. Update:

- `docs/CODEX_HANDOFF.md`
- `docs/NEXT_TASKS.md`
- `docs/CHANGELOG_CONTEXT.md`
- `AGENTS.md`

## Key Files Changed Recently

- `apps/web/src/app/agent/page.tsx`: keeps `conversationIdsRef` in sync with SWR/refetch data and refreshes conversation list for unknown run conversation IDs.
- `apps/api/tests/test_agent_runs_api.py`: forces SQLite and explicit test admin password so API tests do not pick up local `.env` production secrets.
- `docker-compose.prod.yml`: passes `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, and `DEEPSEEK_MODEL` into `api`, `worker-general`, and `worker-video` from `.env`; no secret value is committed.
- `.env`: contains local secrets, including DeepSeek config; never print, stage, or commit.
- `AGENTS.md`, `docs/CODEX_HANDOFF.md`, `docs/NEXT_TASKS.md`, `docs/CHANGELOG_CONTEXT.md`: handoff docs updated.
- `ARCHITECTURE_EVALUATION_REPORT.md`: dirty protected user work; do not touch.

## Database, API, Frontend Status

- Database: production path uses PostgreSQL; local path supports SQLite.
- Queue: production path uses Redis/RQ; inline queue remains for dev.
- Artifact storage: S3/MinIO production path, local/local_shared compatibility retained.
- RAG: pgvector production path exists and passed isolated non-empty validation; production corpus migration is not claimed complete.
- DeepSeek: `.env` has a configured key and compose now forwards it into API/workers. Do not disclose the key.
- API health: after DeepSeek forwarding, `/health/ready` was observed `ok` with Postgres/Redis/queue/S3/pgvector/security. On 2026-07-16, Docker was not running during this handoff check, so current live health could not be reverified.
- Frontend: `npm.cmd run build` passed after the `/agent` frontend state fix.
- Production service startup command should include `--scale worker-general=4 --scale worker-video=2`.

## Known Bugs And Risks

- `/agent` still needs a real browser/API smoke proving submit -> left conversation -> route restore -> real script/video run -> chat writeback.
- Raw `pip-audit` fails unless exact documented `transformers 4.57.6` exceptions are applied.
- Dataset export queue has worker code but no public enqueue API endpoint.
- Standalone dataset/knowledge/blueprint workers are not configured; `worker-general` consumes those queues.
- Existing Redis recovery and worker recovery tests are marker tests, not true automated fault injection.
- P2 Redis pause/recovery, worker crash/restart, 50 video jobs, full MinIO chain, and P3 200/300/500 remain not executed.
- `.env`, runtime, local DBs, logs, uploads, generated secrets, and Docker/MinIO data must not be committed or printed.

## Must Not Break

- Auth, roles, user isolation, admin/audit/permissions.
- Connector, Payload Preview, Debug Replay.
- Dataset, field mapping, clean/export, secure downloads.
- QA/RAG/knowledge base and DeepSeek streaming QA.
- APP SQLite and RAG SQLite separation.
- Video breakdown local Agent real execution, debug payloads, artifacts, result persistence.
- Blueprint publish/test/release gate/import/export/rollback/history.
- SSE first and polling fallback.
- PostgreSQL/Redis/RQ/S3/pgvector production path and SQLite/local dev compatibility.
- Navigation labels: `缇庡畢BI`, `涓囪兘缇庤櫨`.
- Model display: `meizhaiseek 2.0`.

## Read First In Next Window

1. `AGENTS.md`
2. `docs/CODEX_HANDOFF.md`
3. `docs/NEXT_TASKS.md`
4. `docs/CHANGELOG_CONTEXT.md`
5. `docs/TESTING.md`
6. `docs/CAPACITY_REPORT_V18.md`
7. `docs/V183_QUEUE_ACCEPTANCE.md`
8. `docs/V183_PGVECTOR_VALIDATION.md`
9. `docs/SECURITY_EXCEPTIONS.md`
10. `apps/web/src/app/agent/page.tsx`
11. `apps/web/src/components/AgentWorkspace.tsx`
12. `apps/web/src/components/GenericAgentPanel.tsx`
13. `apps/web/src/components/VideoScriptAgentPanel.tsx`
14. `apps/web/src/hooks/useAgentRunEvents.ts`
15. `apps/web/src/hooks/useAgentRunPolling.ts`
16. `apps/api/routers/agent_runs.py`
17. `apps/api/routers/conversations.py`
18. `apps/api/services/conversation_store.py`
19. `apps/api/services/task_store.py`
20. `apps/api/workflows/video_script_workflow.py`
21. `apps/api/tasks/queue.py`
22. `docker-compose.prod.yml`

## v1.8.6 SQL Safety Handoff

- SQL safety scanner: `apps/api/scripts/scan_sql_safety.py`.
- Baseline: `docs/sql_safety_baseline_v186.json`.
- Evidence: `docs/V186_SQL_SAFETY_GUARDRAILS.md`.
- CI now blocks new dynamic SQL findings with `--fail-on-new`.
- Runtime marker closeout: `docs/V186_RUNTIME_HEALTH_MARKERS.md`.

## New Window Prompt

Continue `E:\USE\codexhome\agents-cowork\meizhaiseek-platform` on branch `stabilization/v1.8.3`, current HEAD `d83603213ed34fc315d783a98aa1c51467f288f3`, version `meizhaiseek v1.8.3`, model `meizhaiseek 2.0`. First read `AGENTS.md`, `docs/CODEX_HANDOFF.md`, `docs/NEXT_TASKS.md`, `docs/CHANGELOG_CONTEXT.md`, then inspect `git status --short` and the relevant code. `ARCHITECTURE_EVALUATION_REPORT.md` is protected dirty user work; do not modify, stage, or fix whitespace. Do not commit `.env`, runtime, logs, uploads, models, node_modules, DB files, Docker data, MinIO data, local videos, or Locust raw output. Current dirty functional files include `apps/web/src/app/agent/page.tsx`, `apps/api/tests/test_agent_runs_api.py`, and `docker-compose.prod.yml`; review before editing. Priority is `/agent`: after task submit the left conversation list must add and persist a real conversation; route switching must restore task/chat/run; script/video breakdown must truly execute through backend/local Agent; run status/result/error must write back to the matching chat. Verify with real backend/API or browser smoke, not UI-only state. Preserve auth, Connector, Debug, admin, Dataset, QA/RAG/DeepSeek, SQLite, video breakdown, SSE/polling, Blueprint, Postgres/Redis/RQ/S3/pgvector.
