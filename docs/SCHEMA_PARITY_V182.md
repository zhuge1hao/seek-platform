# Schema Parity v1.8.2

Date: 2026-07-07

## Coded

- Added `apps/api/scripts/verify_schema_parity.py`.
- The script compares the SQLite app schema created by existing migrations with SQLAlchemy/Alembic metadata for critical v1.8.2 tables.
- Covered critical groups: Agent Run, Dataset, Blueprint tables, and `row_version` on `agent_runs`.

## Executed

```powershell
python apps/api/scripts/verify_schema_parity.py --json-report
```

Result: passed.

```json
{
  "status": "passed",
  "missing_tables": [],
  "column_mismatches": [],
  "sqlite_table_count": 22,
  "metadata_table_count": 22
}
```

## Not Executed

- Full PostgreSQL live database reflection parity.
- Alembic downgrade parity.
- Foreign-key semantic comparison beyond the critical columns above.
