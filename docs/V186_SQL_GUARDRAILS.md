# v1.8.6 SQL Guardrails

Version: `meizhaiseek v1.8.6`

Date: 2026-07-17

## Scope

Add guardrails that prevent new unsafe f-string SQL or unexplained `# nosec B608` usage from entering the codebase, while allowing the current historical baseline to shrink over time.

## Planned Checks

- Add `apps/api/scripts/scan_sql_safety.py`.
- Add `docs/sql_safety_baseline_v186.json`.
- Add CI guardrails for `--fail-on-new --baseline docs/sql_safety_baseline_v186.json`.
- Fix 5-10 low-risk/high-signal historical occurrences where a safe parameterized or whitelisted form is straightforward.

## Current Result

- Scanner: `passed`
- Baseline guard: `passed`
- CI gate: `passed`
- Baseline count: 31
- High-risk findings: 0
- Medium-risk findings: 28
- Low-risk findings: 3
- Fixed in v1.8.6: 4 high-risk helper SQL sites in `app_sqlite_migrations.py` and `qa_rag_store.py`.
- Full historical cleanup: `not_run`
