# v1.8.7 pgvector Resume And Top-k

## Status

- Coded: `passed`
- Executed: `passed`
- Passed: `passed`
- Failed: `not_run`

## Required Evidence

- Dry-run, execute, verify.
- Controlled interruption and resume.
- Repeated execute/verify idempotency.
- SQLite top-k vs pgvector top-k comparison.
- Orphan document/chunk/embedding checks.

## Results

Executed in Docker API container on 2026-07-17.

Command:

```powershell
docker compose -f docker-compose.prod.yml exec -T api python scripts/acceptance_pgvector_nonempty.py --json-report --include-resume --include-topk
```

Fixture:

- SQLite path inside container: `/app/apps/api/runtime/acceptance/v187_pgvector/fixture_eeac939b1d.sqlite3`
- Documents: `5`
- Chunks: `60`
- Users: `2`
- Knowledge bases: `2`
- Embedding dimensions: `512`

Migration results:

- Dry-run: `passed`, `document_count=5`, `chunk_count=60`, `orphan_chunk_count=0`, `embedding_dimensions=[512]`.
- Execute: `passed`, `migrated_documents=5`, `migrated_chunks=60`.
- Verify: `passed`.
- Repeat execute: `passed`; `ON CONFLICT` kept migration idempotent and did not duplicate rows.
- Repeat verify: `passed`.

Resume results:

- Controlled interruption command stopped after 10 items and returned `interrupted` with checkpoint count `10`.
- Resume command reused the checkpoint, migrated the remaining `55` chunks, and returned `passed`.
- Verify after resume returned `passed`.
- Source SQLite fixture remained in place under runtime; no destructive source cleanup was performed.

Top-k results:

- Initial generated fixture had periodic vector ties: SQLite and pgvector returned the same top5 set but with different ordering. That failed exact-order comparison and was treated as a fixture-quality issue, not a passed result.
- Fixture generation was changed to hash-derived vectors and rerun.
- SQLite top5 chunk IDs exactly matched pgvector top5 chunk IDs:
  - `chunk_v187_d4cd01502a_0_0`
  - `chunk_v187_d4cd01502a_4_3`
  - `chunk_v187_d4cd01502a_2_9`
  - `chunk_v187_d4cd01502a_4_9`
  - `chunk_v187_d4cd01502a_0_2`
- pgvector query time: `113.573 ms`.

Orphan check:

- Deleted fixture doc: `doc_v187_d4cd01502a_4`
- Deleted chunks: `12`
- Chunks before delete for that user: `36`
- Chunks after delete: `24`
- Result: `passed`; no orphan chunks remained for the deleted document.

Marker:

`PGVECTOR_MIGRATION_VERIFIED` remains eligible for `passed`; v1.8.7 adds resume and top-k evidence to the earlier dry-run/execute/verify proof.
