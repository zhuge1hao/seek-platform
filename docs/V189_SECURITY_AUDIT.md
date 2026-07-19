# v1.8.9 Security Audit

Version: `meizhaiseek v1.8.9`

## pip-audit

- Raw report: `not_run`.
- Gate: `not_run`.
- New focus: `torch 2.12.1` / `GHSA-rrmf-rvhw-rf47`.
- Rule: do not accept the advisory until production image scope, BGE usage, model trust boundary, and upgrade feasibility are checked.

## Existing Accepted Risks

- Local `.venv` `setuptools 81.0.0`: existing short-term accepted risk only when production image uses a fixed setuptools.
- `transformers 4.57.6`: existing exact accepted risks for local BGE embedding path.

## Validation

- `bandit`: `not_run`.
- `pip-audit`: `not_run`.
- `check_pip_audit_report.py`: `not_run`.
