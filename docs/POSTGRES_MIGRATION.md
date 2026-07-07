# PostgreSQL Migration

v1.8 adds SQLAlchemy async, asyncpg, Alembic, and an initial APP schema covering 22 tables.

Key commands:

```powershell
alembic upgrade head
python apps/api/scripts/migrate_sqlite_to_postgres.py --dry-run --json-report
python apps/api/scripts/migrate_sqlite_to_postgres.py --execute --verify
```

The migration script backs up SQLite before execute, never deletes the source DB, and uses conflict-safe inserts rather than silently overwriting existing PostgreSQL rows.

SQLite remains the default development backend. Production should set:

```text
APP_DB_BACKEND=postgres
APP_DATABASE_URL=postgresql+asyncpg://...
```
