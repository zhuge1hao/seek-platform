# v1.8.5 pgvector Non-Empty Acceptance

Version: meizhaiseek v1.8.5
Model: meizhaiseek 2.0

## Status

| Check | Coded | Executed | Result |
| --- | --- | --- | --- |
| Non-empty SQLite fixture support | script entry | not_run | not_run |
| Dry-run migration | existing script | not_run | not_run |
| Execute migration | existing script | not_run | not_run |
| Verify migration | existing script | not_run | not_run |
| Resume after interruption | not yet executed | not_run | not_run |
| Idempotent repeat execute | script entry | not_run | not_run |
| SQLite vs pgvector top-k comparison | not yet executed | not_run | not_run |

## Implemented

- Added `apps/api/scripts/acceptance_pgvector_nonempty.py` as a controlled wrapper around `migrate_rag_sqlite_to_pgvector.py`.
- v1.8.7 extends the script so it can generate an isolated 5-document/60-chunk fixture, simulate checkpoint interruption, resume, repeat execute/verify idempotently, and compare SQLite top-k with pgvector top-k.

## Not Run

No non-empty pgvector migration was executed in this environment because the Docker PostgreSQL/pgvector stack was unavailable.

## Later v1.8.7 Execution

See `docs/V187_PGVECTOR_RESUME_TOPK.md` for the real Docker execution that completed dry-run, execute, verify, resume, idempotency, top-k, and orphan cleanup validation.

## Accepted Risk

`pip-audit` remains mandatory. The existing `transformers 4.57.6` vulnerabilities are not considered resolved unless a future audit returns clean or the accepted-risk entry is updated.
