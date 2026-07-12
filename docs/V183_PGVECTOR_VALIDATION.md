# v1.8.3 pgvector Validation

## Target

- Validate non-empty SQLite RAG to pgvector migration with dry-run, execute, verify, resume, and top-k comparison.

## Current Status

- Executed for v1.8.3 on 2026-07-12 with isolated runtime test data and a temporary PostgreSQL database.

## Executed

- BGE-small-zh smoke: model exists, loads successfully, embedding dimension is 512.
- Prepared non-empty SQLite RAG test data: 5 documents, 60 chunks, `knowledge_base_id=v183-kb`, 512-dimensional embeddings.
- Ran `migrate_rag_sqlite_to_pgvector.py --dry-run --json-report`.
- Ran `migrate_rag_sqlite_to_pgvector.py --execute --batch-size 7 --checkpoint <runtime checkpoint> --json-report`.
- Ran `migrate_rag_sqlite_to_pgvector.py --verify --json-report`.
- Ran resume/idempotency check with `--execute --resume --checkpoint <runtime checkpoint> --json-report`.
- Ran pgvector top-k search against the migrated data.

## Passed

- Dry-run: 5 documents, 60 chunks, 0 orphan chunks, embedding dimension `[512]`.
- Execute: migrated 5 documents and 60 chunks.
- Verify: pgvector contained 5 documents and 60 chunks.
- Resume: migrated 0 additional documents and 0 additional chunks, confirming checkpoint idempotency.
- Top-k search returned 3 results; the nearest result was `v183-doc-0`, matching the deterministic test vector.

## Not Executed

- Production-data pgvector migration.
- Full BGE-generated 50-200 chunk corpus migration; v1.8.3 used deterministic 512-dimensional embeddings for migration and separate BGE smoke for model loading/dimension.

## Environment Limits

- The test used an isolated temporary PostgreSQL database and runtime SQLite file; test data and checkpoint are not committed.
