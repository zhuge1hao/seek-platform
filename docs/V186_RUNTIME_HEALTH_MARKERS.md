# v1.8.6 Runtime Health Markers

Version: meizhaiseek v1.8.6
Model: meizhaiseek 2.0
Date: 2026-07-17

Runtime marker values must reflect only executed evidence. `.env` is not committed.

| Marker | v1.8.6 value | Evidence |
| --- | --- | --- |
| `WORKER_RECOVERY_VERIFIED` | `passed` | v1.8.4 P1 evidence, commit `2edcfd2215dfd8978b8ffb129b26ccde35921bf3` |
| `VIDEO_QUEUE_50_VERIFIED` | `passed` | v1.8.4 P1 evidence, commit `2edcfd2215dfd8978b8ffb129b26ccde35921bf3` |
| `REDIS_RECOVERY_VERIFIED` | `passed` | v1.8.4 P1 evidence, commit `2edcfd2215dfd8978b8ffb129b26ccde35921bf3` |
| `DATASET_QUEUE_VERIFIED` | `passed` | `docs/V186_ACCEPTANCE_EXECUTION_REPORT.md`, commit `9af9da1aec6edae33f4b53be8362972accde49ee` |
| `KNOWLEDGE_QUEUE_VERIFIED` | `failed` | `docs/V186_ACCEPTANCE_EXECUTION_REPORT.md`, 5 uploads did not reach ready/chunked state within 180 seconds |
| `BLUEPRINT_QUEUE_VERIFIED` | `passed` | `docs/V186_ACCEPTANCE_EXECUTION_REPORT.md`, commit `9af9da1aec6edae33f4b53be8362972accde49ee` |
| `ARTIFACT_S3_VERIFIED` | `not_run` | MinIO was only partially checked; TTL, cross-user denial, 10MB/100MB streaming were not fully executed |
| `PGVECTOR_MIGRATION_VERIFIED` | `passed` | `docs/V186_ACCEPTANCE_EXECUTION_REPORT.md`, dry-run/execute/verify/repeat verify completed in API container |
| `BROWSER_AGENT_SMOKE_VERIFIED` | `not_run` | Browser tool or Playwright smoke was not available/executed |
| `CAPACITY_LAST_VERIFIED_USERS` | `100` | Last true capacity evidence remains the prior 100-user result; no 200/300/500 run in v1.8.6 |
| `CAPACITY_LAST_TEST_PASSED` | `passed` | Prior 100-user gate evidence only |

## P4 Coverage Evidence

Existing and v1.8.6 tests cover `_PostgresPool`, cache, Redis service, rate limiting, runtime health markers, and the agent run event bus:

- `apps/api/tests/test_app_sqlite.py`
- `apps/api/tests/test_cache_and_rate_limit.py`
- `apps/api/tests/test_sql_guardrails.py`
- `apps/api/tests/test_sql_safety_scanner.py`

Latest local gate:

- `python -m unittest discover -s apps/api/tests`: 80 tests OK.
- `python -m pytest apps/api/tests`: 80 passed, 2 skipped.
- `bandit --severity-level medium -r apps/api`: passed with High=0, Medium=0.

## Not Executed

- 200/300/500 user capacity.
- Full browser Agent smoke.
- Full MinIO TTL and 10MB/100MB streaming matrix.
- Knowledge queue successful end state.

## Accepted Risk

- Runtime marker env pass-through exists in the local dirty `docker-compose.prod.yml` but remains uncommitted in this run.
- `ARTIFACT_S3_VERIFIED` stays `not_run` because only partial artifact HTTP checks passed.
