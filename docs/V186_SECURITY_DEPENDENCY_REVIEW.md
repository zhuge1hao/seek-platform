# v1.8.6 Security Dependency Review

Version: `meizhaiseek v1.8.6`

Date: 2026-07-17

## Scope

Review the real `pip-audit` output for v1.8.6, clear the `setuptools` vulnerability if a safe upgrade is possible, and update exact accepted-risk entries for the `transformers` dependency chain if a safe BGE/RAG-compatible upgrade is not proven.

## Initial Known Items

- `setuptools 81.0.0`: one advisory was observed before v1.8.6; target is upgrade to the recommended safe version.
- `transformers 4.57.6`: four advisories were observed before v1.8.6 through the `sentence-transformers` local embedding path.

## Required Evidence

- Raw `pip-audit` JSON stored under runtime logs and not committed.
- Gate result from `apps/api/scripts/check_pip_audit_report.py`.
- BGE/RAG smoke evidence if `sentence-transformers` or `transformers` is upgraded.
- `docs/SECURITY_EXCEPTIONS.md` updated with exact advisory IDs, review date, and expiry for every accepted risk.

## Current Result

`not_run`
