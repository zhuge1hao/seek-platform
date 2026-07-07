# meizhaiseek v1.8.1 Security Hardening

Date: 2026-07-06

## Completed

- Removed production fallback to the public JWT development secret. Production-like mode (`APP_ENV=production` or `APP_DB_BACKEND=postgres`) now requires `AUTH_TOKEN_SECRET`.
- Local development without `AUTH_TOKEN_SECRET` generates `apps/api/runtime/security/generated_secrets.json`; runtime health reports only `configured`, `generated`, or `invalid`.
- Removed production use of `admin123`; production requires a strong `INITIAL_ADMIN_PASSWORD` / `MEIZHAISEEK_ADMIN_INITIAL_PASSWORD`. Existing admins are not overwritten.
- Runtime health reports `default_admin_password_detected` without exposing passwords.
- `app_sqlite.table_count()` now validates table names against an allowlist before building SQL.
- Local CLI connector execution uses `shlex.split()` and `shell=False`, rejecting common shell metacharacters.
- Silent event/conversation failure paths now log sanitized warning records.
- SHA1-generated migration/file IDs were replaced with SHA256 in dataset and legacy JSON migration paths.
- Vulnerable direct dependencies were upgraded: FastAPI, Starlette via FastAPI, python-multipart, requests, pytest, pytest-asyncio.

## Verified

- `python -m compileall apps/api`: passed.
- `python -m unittest discover -s apps/api/tests`: 35 tests passed.
- `python -m pytest apps/api/tests`: 35 tests passed.
- `ruff check apps/api`: passed.
- `bandit -r apps/api -x apps/api/tests,apps/api/runtime,apps/api/models`: high severity count is 0; medium/low findings remain for dynamic SQL patterns and guarded subprocess usage.
- `pip-audit`: direct dependency advisories reduced from 19 to 3; remaining advisories are in `transformers 4.57.6`, constrained by `sentence-transformers<5`.

## Not Complete

- `mypy` is not yet a passing gate. The current package layout uses top-level `services` / `tasks` imports and needs scoped mypy configuration plus type fixes.
- Bandit medium findings still need per-query review or exact `# nosec` annotations where query fragments are proven allowlisted/static.

## v1.8.2 P1 Update

Executed on 2026-07-06:

- Scoped mypy is now configured in `pyproject.toml` with `mypy_path=apps/api` and passed for the selected services, tasks, storage, rag, and db modules.
- Bandit JSON report was generated at `apps/api/runtime/logs/bandit-v182.json`.
- Bandit result: High=0, Medium=0, Low=33.
- `apps/api/scripts/check_bandit_report.py` passed and blocks High/Medium findings in the generated JSON.
- Raw `pip-audit` remains 未通过 because `transformers 4.57.6` has 3 advisories.
- `apps/api/scripts/check_pip_audit_report.py` passed only for exact documented temporary exceptions in `docs/SECURITY_EXCEPTIONS.md`.

Not executed:

- sentence-transformers 5.x / transformers 5.x compatibility upgrade.
- BGE-small-zh embedding smoke after dependency upgrade.
- SQLite RAG and pgvector retrieval smoke after dependency upgrade.
