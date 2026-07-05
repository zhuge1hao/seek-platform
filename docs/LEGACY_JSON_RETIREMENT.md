# Legacy JSON Retirement

v1.7.2 keeps legacy JSON recovery code available only behind `APP_LEGACY_JSON_FALLBACK=true`.

Production defaults must keep `APP_LEGACY_JSON_FALLBACK=false`. Normal request paths read APP SQLite and RAG SQLite. Fallback usage is counted by runtime health through `legacy_json_fallback_usage_count` and `legacy_json_fallback_last_used_at`.

Run `python apps/api/scripts/verify_sqlite_migration_complete.py` to verify APP SQLite tables, indexes, user data, current SQLite-backed surfaces, and unmigrated legacy JSON warnings. Use `--json` for machine-readable output.
