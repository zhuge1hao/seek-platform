# v1.8.8 Security And SQL Risk

Version: `meizhaiseek v1.8.8`
Model: `meizhaiseek 2.0`

## Status

- raw pip-audit: `failed` on 2026-07-19 with 6 known vulnerabilities in 3 packages; raw JSON is stored under `apps/api/runtime/logs/` and is not committed.
- pip-audit exact exception gate: `failed` because `torch 2.12.1` / `GHSA-rrmf-rvhw-rf47` is a new, undocumented advisory.
- Existing accepted risks: `setuptools 81.0.0` / `PYSEC-2026-3447`; `transformers 4.57.6` / `PYSEC-2025-217`, `PYSEC-2026-2290`, `PYSEC-2026-2288`, `PYSEC-2026-2289`.
- SQL safety scan: `passed` with `finding_count=31`, `high=0`, and no new findings against `docs/sql_safety_baseline_v186.json`.
- follow_imports review: `not_run`; do not change global `follow_imports = "skip"` without scoped evidence.

## Commands

```powershell
python -m pip_audit --format json > apps/api/runtime/logs/pip_audit_v188_raw.json
python apps/api/scripts/check_pip_audit_report.py apps/api/runtime/logs/pip_audit_v188_raw.json
python apps/api/scripts/scan_sql_safety.py --json-report --fail-on-new --baseline <baseline>
```

Do not submit runtime logs or raw audit output.
