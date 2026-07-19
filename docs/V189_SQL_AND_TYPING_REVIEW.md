# v1.8.9 SQL And Typing Review

Version: `meizhaiseek v1.8.9`

## SQL Safety

- Baseline: `31`.
- High risk: `0`.
- Scan command: `python apps/api/scripts/scan_sql_safety.py --json-report --fail-on-new --baseline docs/sql_safety_baseline_v186.json`.
- Result: `passed`.
- Finding count: `31`, unchanged from the baseline.
- Counts by risk: `medium=28`, `low=3`, `high=0`.
- Baseline movement: unchanged; it did not increase.
- Local fixes: `not_run`; the 31 findings are existing documented `B608` dynamic SQL review points with no new high-risk item. No large store refactor was attempted in this cycle.

## follow_imports

- Current setting: `follow_imports = "skip"`.
- Review status: `passed`.
- Targeted tightening: `pydantic.*` now uses `follow_imports = "normal"` via a module override.
- Validation: `.venv\Scripts\python.exe -m mypy apps/api` passed with `199` source files and no issues.
- Coverage impact: current mypy coverage was not reduced.

Third-party modules observed in `apps/api` imports and affected by the global skip posture include:

- `fastapi`
- `openpyxl`
- `pydantic`
- `pytest`
- `requests`
- `rq`
- `sqlalchemy`
- `starlette`
- `xlrd`

Modules not tightened in this cycle:

- `fastapi` / `starlette`: deferred because framework internals and testclient deprecations are noisy and not directly related to the v1.8.9 risk target.
- `sqlalchemy`: deferred to a repository typing pass because the current sync/async database adapter has broader inferred types to review.
- `openpyxl`, `xlrd`, `rq`, `requests`, `pytest`: left under the global setting for now; they are candidates for narrow overrides after the 200-user submit path is profiled.
