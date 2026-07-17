# v1.8.6 Acceptance Execution Report

Version: `meizhaiseek v1.8.6`

Date: 2026-07-17

## Docker Prerequisite

Docker Desktop Linux Engine recovered successfully. Production compose was rebuilt and started with PostgreSQL, Redis, MinIO, API, Web, Nginx, `worker-general=4`, and `worker-video=2`.

## Dataset Queue

Status: `passed`

Executed:

- `python apps/api/scripts/acceptance_dataset_queue.py --json-report`
- Report: `apps/api/runtime/logs/v186_dataset_acceptance_rerun.json` (not committed).

Evidence:

- Dataset discovered: `dataset_20260629092423_409f328a`.
- `dataset_clean` enqueued: `dataset_job_20260717081802_4349eb63`.
- `dataset_export` enqueued: `dataset_job_20260717081802_da04b35e`.
- Cancel path returned `cancelled`.
- Retry path enqueued `dataset_job_20260717081802_bb5464ef`.
- Worker logs show dataset jobs completed.

Limitations:

- Cross-user Dataset artifact isolation was not fully exercised by this script.

## Knowledge Queue

Status: `failed`

Executed:

- Initial run: `python apps/api/scripts/acceptance_knowledge_queue.py --json-report --cleanup`.
- Rerun after fixing RQ job IDs and temporarily copying the local BGE model into API/worker containers.
- Reports under `apps/api/runtime/logs/` are not committed.

Evidence:

- Initial run failed because RQ rejected job IDs containing `:`.
- Code fix changed Knowledge job IDs to `document-ingest-<doc_id>` and `document-reindex-<doc_id>`.
- Rerun uploaded 5 generated non-sensitive `.md` seed documents and enqueued 5 `document-ingest-*` jobs.
- Worker accepted Knowledge jobs, but the script did not observe 5 ready documents with non-zero chunks within 180 seconds.

Current result:

- `failed`; do not set `KNOWLEDGE_QUEUE_VERIFIED=passed`.

## Blueprint Queue

Status: `passed`

Executed:

- `python apps/api/scripts/acceptance_blueprint_queue.py --json-report`
- Report: `apps/api/runtime/logs/v186_blueprint_acceptance_rerun.json` (not committed).

Evidence:

- Blueprint discovered: `bp_video_script_breakdown`.
- Test case discovered: `bpt_bf58862c8156`.
- Test run enqueued: `bptr_8fa8a4206632`.
- Queue job: `blueprint-test-bptr_8fa8a4206632`.
- Worker logs show the blueprint job completed.
- Release gate returned `allowed=false`, correctly blocking release because latest test result was not a pass.

## MinIO / Artifact Storage

Status: `partial`

Executed:

- `python apps/api/scripts/acceptance_minio_storage.py --json-report --run-id run_20260716101438_4389785c --artifact-id artifact_2c7b44d5c482 --size 10MB`
- Report: `apps/api/runtime/logs/v186_minio_acceptance.json` (not committed).

Passed:

- Authenticated signed URL route returned HTTP 200 for an S3 artifact.
- Authenticated streaming download route returned HTTP 200.
- S3 secret/access key was not returned in the signed URL response body.

Not run:

- TTL expiry after waiting beyond the signed URL lifetime.
- User B cross-user denial.
- Object key path traversal rejection.
- Fresh 10MB/100MB streaming upload/download.
- Chinese filename download check.

Do not set `ARTIFACT_S3_VERIFIED=passed` from this partial result alone.

## pgvector Non-Empty Migration

Status: `passed`

Executed:

- Generated isolated SQLite fixture under `apps/api/runtime/logs/v186_pgvector_fixture.sqlite3` with 5 docs, 60 chunks, 2 users, 2 knowledge base IDs, and 512-dimensional embeddings.
- Host dry-run passed.
- Host execute failed because PostgreSQL was not published on host port 5432.
- Copied fixture into the API container and executed migration on the Docker network.

Container evidence:

- Dry-run: `passed`, `document_count=5`, `chunk_count=60`, `embedding_dimensions=[512]`.
- Execute: `passed`, `migrated_documents=5`, `migrated_chunks=60`.
- Verify: `passed`.
- Repeat verify: `passed`.

Not run:

- Explicit interrupted resume test.
- SQLite vs pgvector top-k comparison.

## Browser Agent Smoke

Status: `not_run`

Reason:

- No browser-control MCP was available in this session.
- Project did not have Playwright installed in `apps/web/node_modules`.
- No browser result is claimed.

## Runtime Markers

Set to `passed` only where full evidence exists:

- `DATASET_QUEUE_VERIFIED`: eligible for `passed`.
- `BLUEPRINT_QUEUE_VERIFIED`: eligible for `passed`.
- `PGVECTOR_MIGRATION_VERIFIED`: eligible for `passed` with resume/top-k limitations noted.

Remain `not_run` or `failed`:

- `KNOWLEDGE_QUEUE_VERIFIED=failed`.
- `ARTIFACT_S3_VERIFIED=not_run` for full acceptance; partial signed-url/download evidence only.
- `BROWSER_AGENT_SMOKE_VERIFIED=not_run`.

Runtime marker closeout: `docs/V186_RUNTIME_HEALTH_MARKERS.md`.
