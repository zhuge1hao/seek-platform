# v1.8.7 Knowledge Queue Fix

## Status

- Coded: `in_progress`
- Executed: `not_run`
- Passed: `not_run`
- Failed: `not_run`

## Root Cause

v1.8.6 acceptance treated only `ready` documents as successful. The backend ingest service writes successful documents as `completed`, and both SQLite and pgvector retrieval paths already treat `ready` and `completed` as searchable terminal states.

## Fix

- `acceptance_knowledge_queue.py` accepts `ready` and `completed` when `chunk_count > 0`.
- SQLite RAG schema guardrails allow the legacy migration columns that `init_db()` already adds.

## Evidence

Real Docker acceptance output will be recorded here after `python apps/api/scripts/acceptance_knowledge_queue.py --json-report` runs.
