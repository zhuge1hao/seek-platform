# RAG Backends
## v1.8.8 RAG Boundary

No RAG backend redesign is included in v1.8.8. Capacity tests must avoid mixing uncontrolled external embedding latency into platform capacity results, and multi-instance SSE must share the same configured RAG backend.

## v1.8.4 pgvector Status

- Non-empty migration dry-run: `not_run`
- Non-empty migration execute: `not_run`
- Verify: `not_run`
- Interrupted resume: `not_run`
- Top-k comparison: `not_run`

Do not mark pgvector migration `passed` for v1.8.4 until `docs/V184_PGVECTOR_NONEMPTY_VALIDATION.md` contains real command output and counts.

## v1.8.3 pgvector Validation - 2026-07-12

Encoded:

- `migrate_rag_sqlite_to_pgvector.py` remains the migration entrypoint and supports dry-run, execute, verify, resume, checkpoint, batch size, and JSON report modes.

Executed:

- BGE-small-zh smoke on current dependency stack: model loaded and embedding dimension was 512.
- Non-empty migration validation using isolated runtime SQLite and a temporary PostgreSQL database: 5 documents, 60 chunks, embedding dimension 512.
- Migration modes executed: `--dry-run`, `--execute --batch-size 7 --checkpoint`, `--verify`, and `--execute --resume --checkpoint`.
- pgvector top-k search executed against migrated data.

Passed:

- Dry-run reported 5 documents, 60 chunks, 0 orphan chunks, and embedding dimension `[512]`.
- Execute migrated 5 documents and 60 chunks.
- Verify reported 5 pgvector documents and 60 pgvector chunks.
- Resume migrated 0 additional rows, confirming checkpoint idempotency after a complete run.
- Top-k search returned 3 results; the nearest result matched the deterministic test document.

Not executed:

- Production RAG corpus migration.
- Post-upgrade RAG regression on `sentence-transformers` 5.x / `transformers` 5.x.

Accepted risk:

- The current production dependency set still uses `transformers 4.57.6` behind exact documented pip-audit exceptions; see `docs/SECURITY_EXCEPTIONS.md`.

## v1.8.2 pgvector Validation - 2026-07-10

Encoded:

- `migrate_rag_sqlite_to_pgvector.py` supports `--dry-run`, `--execute`, `--verify`, `--batch-size`, `--resume`, `--checkpoint`, and `--json-report`.
- The script preserves document IDs, chunk IDs, user IDs, metadata, embedding dimensions, and the configured embedding model name.

Executed:

- BGE-small-zh smoke on current dependency stack: model loaded, embedding dimension was 512.
- SQLite RAG retrieval smoke: inserted one document/chunk and retrieved it with top-k search.
- pgvector retrieval smoke: inserted one document/chunk and retrieved it with top-k search, then deleted the temporary document.
- Non-empty migration smoke using an isolated temporary RAG SQLite source: 5 documents, 50 chunks, embedding dimension 512.
- Migration modes executed: `--dry-run`, `--execute --batch-size 7`, `--verify`, and `--execute --resume --checkpoint`.

Passed:

- Non-empty dry-run reported 5 documents and 50 chunks.
- Execute migrated 5 documents and 50 chunks.
- Verify reported 5 pgvector documents and 50 pgvector chunks.
- Resume with a pre-populated checkpoint migrated the remaining 4 documents and 40 chunks.

Not executed:

- Large production RAG corpus migration.
- Full top-k statistical difference report across many queries.

v1.8 introduces a RAG provider facade.

Backends:

- `RAG_BACKEND=sqlite`: existing local RAG SQLite path and default.
- `RAG_BACKEND=pgvector`: production target placeholder.

Current status: SQLite remains the working implementation. pgvector is reported as not migrated and must not be described as complete until document/chunk/vector writes and reads move behind the provider.
# v1.8.5 pgvector Status

- `apps/api/scripts/acceptance_pgvector_nonempty.py` wraps dry-run, execute, verify, and repeat verify for non-empty migration reruns.
- Non-empty pgvector migration, resume, and top-k comparison are `not_run` for v1.8.5 in the current environment because Docker PostgreSQL/pgvector was unavailable.
- Production mode must not silently fall back to SQLite when `RAG_BACKEND=pgvector`.
# v1.8.7 Knowledge Queue Note

- Production Knowledge acceptance requires API and worker-general containers to see the same local BGE model directory.
- v1.8.7 compose mounts `./apps/api/models` to `/app/models:ro` and sets `BGE_SMALL_ZH_MODEL_PATH=/app/models/bge-small-zh`.
- Successful document statuses `ready` and `completed` are both searchable terminal states for SQLite and pgvector RAG.

# v1.8.7 pgvector Resume And Top-k

Status: `passed` on 2026-07-17.

- `acceptance_pgvector_nonempty.py` now creates an isolated non-sensitive SQLite fixture when `--sqlite-path` is omitted.
- Fixture shape: 5 documents, 60 chunks, 2 users, 2 knowledge bases, 512-dimensional embeddings.
- Migration modes executed in Docker API container: dry-run, execute, verify, repeat execute, repeat verify.
- Resume executed with a controlled checkpoint interruption after 10 items, then completed the remaining rows.
- SQLite top-k and pgvector top-k returned the same ordered top5 after hash-derived fixture vectors removed artificial ties.
- Delete cleanup removed 12 chunks for the deleted fixture document and left no orphan chunks for that document.

Evidence: `docs/V187_PGVECTOR_RESUME_TOPK.md`.

The current raw pip-audit risk remains in the `transformers 4.57.6` embedding dependency path; the exact exception gate passed, and no Transformers 5.x upgrade is claimed.
