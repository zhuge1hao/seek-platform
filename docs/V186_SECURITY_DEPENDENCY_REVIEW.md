# v1.8.6 Security Dependency Review

Version: `meizhaiseek v1.8.6`

Date: 2026-07-17

## Scope

Review the real `pip-audit` output for v1.8.6, clear the `setuptools` vulnerability if a safe upgrade is possible, and update exact accepted-risk entries for the `transformers` dependency chain if a safe BGE/RAG-compatible upgrade is not proven.

## Executed

- Raw audit command: `.venv\Scripts\python.exe -m pip_audit --format json`.
- Raw audit output: stored at `apps/api/runtime/logs/pip_audit_v186_raw.json` and not committed.
- Raw result before remediation attempt: `failed`, 5 advisories.
- Attempted `setuptools==83.0.0`: raw audit dropped to 4 advisories, but `pip check` failed because `torch 2.12.1` requires `setuptools<82`.
- Reverted local venv to `setuptools==81.0.0`; `pip check` returned clean.
- Updated `apps/api/scripts/check_pip_audit_report.py` to allow only exact package/advisory pairs with expiry dates.
- Updated CI to generate a raw pip-audit JSON report and run the gate script instead of relying on broad CLI ignores.
- Checked package index: `sentence-transformers` latest observed `5.6.0`; `transformers` latest observed `5.14.1`.
- Reran raw audit with UTF-8 JSON redirection: raw exit `1`, 5 advisories.
- Reran gate script against `apps/api/runtime/logs/pip_audit_v186_raw.json`: gate exit `0`.

## Advisory Review

| Package | Version | Advisory | Fix version | Status | Reason |
| --- | --- | --- | --- | --- | --- |
| `setuptools` | `81.0.0` | `PYSEC-2026-3447` | `83.0.0` | accepted risk until 2026-08-17 | Direct upgrade breaks current `torch 2.12.1` metadata constraint. |
| `transformers` | `4.57.6` | `PYSEC-2025-217` | none listed | accepted risk until 2026-09-17 | Dependency is reached through local BGE embedding path; no untrusted checkpoint/trainer flow is exposed. |
| `transformers` | `4.57.6` | `PYSEC-2026-2290` | none listed | accepted risk until 2026-09-17 | Same local embedding scope; upgrade requires BGE/RAG compatibility proof. |
| `transformers` | `4.57.6` | `PYSEC-2026-2288` | `5.0.0` | accepted risk until 2026-09-17 | Fix path requires Transformers 5.x and full embedding/RAG smoke. |
| `transformers` | `4.57.6` | `PYSEC-2026-2289` | `5.3.0` | accepted risk until 2026-09-17 | Fix path requires Transformers 5.3+ and full embedding/RAG smoke. |

## Required Evidence

- Raw `pip-audit` JSON stored under runtime logs and not committed.
- Gate result from `apps/api/scripts/check_pip_audit_report.py`.
- BGE/RAG smoke evidence if `sentence-transformers` or `transformers` is upgraded.
- `docs/SECURITY_EXCEPTIONS.md` updated with exact advisory IDs, review date, and expiry for every accepted risk.

## Current Result

- Raw pip-audit: `failed`.
- Gate result with exact accepted exceptions: `passed`.
- setuptools vulnerability: `failed` to clear safely; recorded as short-term accepted risk.
- transformers vulnerabilities: accepted risk pending a later `sentence-transformers` / `transformers` / BGE/RAG upgrade smoke.
