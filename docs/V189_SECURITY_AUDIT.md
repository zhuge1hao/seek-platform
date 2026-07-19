# v1.8.9 Security Audit

Version: `meizhaiseek v1.8.9`

## pip-audit

- Raw report: `failed`, 4 known vulnerabilities in 1 package.
- Gate: `passed`.
- New focus: `torch 2.12.1` / `GHSA-rrmf-rvhw-rf47`.
- Result: cleared by upgrading local `.venv` to `torch 2.13.0`; production API image already used `torch 2.13.0`.
- BGE smoke after local upgrade: `success bge-small-zh 512`.

## Existing Accepted Risks

- Local `.venv` `setuptools 81.0.0`: cleared by upgrading local `.venv` to `setuptools 83.0.0`.
- `transformers 4.57.6`: existing exact accepted risks for local BGE embedding path.

## Validation

- `compileall`: `passed`.
- `ruff`: `passed`.
- `mypy`: `passed`, including the new `pydantic.*` `follow_imports = "normal"` override.
- `unittest`: `passed`, 91 tests.
- `pytest`: `passed`, 91 passed / 2 skipped.
- `bandit`: `passed` for medium+ severity; no medium or high issues identified.
- `pip-audit`: `failed`, only existing `transformers 4.57.6` advisories remain.
- `check_pip_audit_report.py`: `passed`.
- SQL safety scan: `passed`, baseline `31`, high-risk count `0`.
