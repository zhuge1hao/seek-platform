# v1.8.4 pgvector Non-Empty Migration Validation

Version: `meizhaiseek v1.8.4`
Status: `not_run`

## Required Data

- At least 5 documents.
- At least 50-200 chunks.
- Real or controlled embeddings with consistent dimension.

## Required Commands

- `python apps/api/scripts/migrate_rag_sqlite_to_pgvector.py --dry-run --json-report`
- `python apps/api/scripts/migrate_rag_sqlite_to_pgvector.py --execute --batch-size 500 --json-report`
- `python apps/api/scripts/migrate_rag_sqlite_to_pgvector.py --verify --json-report`
- Interrupted resume validation.

## Results

- Dry run: `not_run`
- Execute: `not_run`
- Verify: `not_run`
- Resume: `not_run`
- Top-k comparison: `not_run`

