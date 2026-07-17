# v1.8.7 Knowledge Queue Fix

## Status

- Coded: `passed`
- Executed: `passed`
- Passed: `passed`
- Failed: `not_run`

## Root Cause

v1.8.6 acceptance treated only `ready` documents as successful. The backend ingest service writes successful documents as `completed`, and both SQLite and pgvector retrieval paths already treat `ready` and `completed` as searchable terminal states.

## Fix

- `acceptance_knowledge_queue.py` accepts `ready` and `completed` when `chunk_count > 0`.
- SQLite RAG schema guardrails allow the legacy migration columns that `init_db()` already adds.
- Production compose mounts `apps/api/models` read-only into API and worker-general containers and pins `BGE_SMALL_ZH_MODEL_PATH=/app/models/bge-small-zh`.

## Evidence

- Docker status: production compose healthy with PostgreSQL, Redis, MinIO, API, Web, Nginx, `worker-general` x4, and `worker-video` x2.
- BGE smoke in `worker-general`: model path `/app/models/bge-small-zh`, exists `true`, files `15`, loadable `true`, dimension `512`.
- Command: `python apps/api/scripts/acceptance_knowledge_queue.py --json-report`.
- Result: `passed`.
- Test user: temporary `accept_v187_*` admin created for acceptance only; password not recorded.
- Documents uploaded: `5`.
- Final ready-equivalent documents: `5`.
- Document IDs: `doc_20260717090831_b87b7459`, `doc_20260717090831_ca680a78`, `doc_20260717090831_1c76ab46`, `doc_20260717090831_a42d487f`, `doc_20260717090831_bde5d4e9`.
- Chunks: `11` per document, `55` total.
- Reindex: `document-reindex-doc_20260717090831_b87b7459`, final status `completed`, chunk count `11`.
- Top-k retrieval: `/api/qa/test-retrieval`, status `success`, `source_count=5`.
- Artifact/storage: not applicable to Knowledge ingest.
- Secrets: no token, password, API key, or full document body recorded in docs.
