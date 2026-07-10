# v1.8.2 pgvector Validation

Date: 2026-07-10

## Executed

- BGE-small-zh model load.
- Embedding generation.
- Dimension check.
- SQLite RAG top-k retrieval smoke.
- pgvector top-k retrieval smoke.
- Non-empty SQLite-to-pgvector migration smoke.
- Resume checkpoint smoke.

## Passed

- Embedding dimension: 512.
- SQLite retrieval returned the inserted chunk.
- pgvector retrieval returned the inserted chunk.
- Migration dry-run: 5 documents, 50 chunks.
- Migration execute: migrated 5 documents, 50 chunks.
- Migration verify: 5 pgvector documents, 50 pgvector chunks.
- Resume checkpoint: migrated remaining 4 documents, 40 chunks.

## Not Executed

- Full production RAG corpus migration.
- Large query-set top-k difference report.

## Accepted Risk

- The transformers dependency advisory exception remains documented in `docs/SECURITY_EXCEPTIONS.md`.
