# RAG Backends

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
