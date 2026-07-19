# v1.8.9 SQL And Typing Review

Version: `meizhaiseek v1.8.9`

## SQL Safety

- Baseline: `31`.
- High risk: `not_run`.
- Scan command: `python apps/api/scripts/scan_sql_safety.py --json-report --fail-on-new --baseline docs/sql_safety_baseline_v186.json`.

## follow_imports

- Current setting: `follow_imports = "skip"`.
- Review status: `not_run`.
- Rule: attempt one targeted module tightening only if it does not reduce current mypy coverage or create broad low-value errors.
