# v1.8.6 SQL Safety Guardrails

Version: meizhaiseek v1.8.6
Model: meizhaiseek 2.0
Date: 2026-07-17

## Status

| Area | Status | Evidence |
| --- | --- | --- |
| SQL scanner implemented | passed | `apps/api/scripts/scan_sql_safety.py` |
| Baseline generated | passed | `docs/sql_safety_baseline_v186.json` |
| CI fail-on-new gate | passed | `.github/workflows/ci.yml` |
| High-risk unguarded helper SQL | passed | 4 high-risk helper sites reduced to 0 high-risk findings |
| Full historical dynamic SQL cleanup | not_run | Remaining baseline retained for staged migration |

## Executed

- `python apps/api/scripts/scan_sql_safety.py --json-report`
- `python apps/api/scripts/scan_sql_safety.py --json-report --fail-on-new --baseline docs/sql_safety_baseline_v186.json`

## Results

- Baseline findings: 31
- High risk findings: 0
- Medium risk findings: 28
- Low risk findings: 3
- Fixed in v1.8.6: 4 high-risk helper sites in `app_sqlite_migrations.py` and `qa_rag_store.py`.

## Guardrail Policy

- New dynamic SQL not present in `docs/sql_safety_baseline_v186.json` fails CI.
- New `# nosec B608` must include a narrow reason and enter the baseline through review.
- Table, column, order, and where clause structure must come from local constants or explicit allowlists.
- Values must remain parameterized.

## Remaining Migration Plan

1. Replace placeholder-list SQL in `apps/api/routers/agents.py` with helper-built parameter lists and stronger comments.
2. Move dataset/test-run dynamic predicates into shared fixed-clause builders.
3. Audit RAG `where` builders and pgvector query construction.
4. Reduce the baseline count on each release; baseline increases require a documented exception.

## Accepted Risk

The remaining 31 findings are accepted only as a baseline for v1.8.6 because CI now blocks expansion. This is not a claim that historical dynamic SQL has been fully eliminated.
