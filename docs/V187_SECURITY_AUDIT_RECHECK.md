# v1.8.7 Security Audit Recheck

## Status

- Raw pip-audit: `failed`
- Gate pip-audit: `passed`
- Accepted risk review: `passed`

## Scope

- Recheck `setuptools` advisory status.
- Recheck `transformers` advisories used by local BGE embeddings.
- Keep exact, unexpired exceptions only.

## Results

Executed on 2026-07-17.

Commands:

```powershell
.venv\Scripts\python.exe -m pip_audit --format json > apps/api/runtime/logs/pip_audit_v187_raw.json
.venv\Scripts\python.exe apps/api/scripts/check_pip_audit_report.py apps/api/runtime/logs/pip_audit_v187_raw.json
.venv\Scripts\python.exe -m pip check
docker compose -f docker-compose.prod.yml exec -T api python -m pip check
```

Raw result:

- `pip-audit` exit code: `1`.
- Vulnerabilities: `5` known advisories in `2` packages.
- `setuptools 81.0.0`: `PYSEC-2026-3447`, fix version `83.0.0`.
- `transformers 4.57.6`: `PYSEC-2025-217`, `PYSEC-2026-2290`, `PYSEC-2026-2288`, `PYSEC-2026-2289`.

Gate result:

- `apps/api/scripts/check_pip_audit_report.py apps/api/runtime/logs/pip_audit_v187_raw.json`: `passed`.
- The gate was updated to read UTF-8, UTF-8-SIG, and UTF-16 JSON because PowerShell redirection writes UTF-16 by default on this host.
- New or expired advisories still fail the gate.

Dependency review:

- Local `.venv`: `setuptools 81.0.0`, `torch 2.12.1`, `sentence-transformers 3.3.1`, `transformers 4.57.6`; `pip check` passed.
- Production API container: `setuptools 83.0.0`, `torch 2.13.0`, `sentence-transformers 3.3.1`, `transformers 4.57.6`; `pip check` passed.
- PyPI check on 2026-07-17 showed `setuptools 83.0.0` as the current fix path and `sentence-transformers` with a current 5.x line. Upstream release notes indicate Sentence Transformers 5.x has a Transformers 5 support path, but this project did not upgrade without a full BGE/RAG smoke on the new stack.

Accepted risk:

- Local/dev `setuptools 81.0.0` is accepted only until 2026-08-17 because upgrading the local environment previously conflicted with `torch 2.12.1`. Production API image evidence shows `setuptools 83.0.0`.
- `transformers 4.57.6` remains accepted only for the local BGE-small-zh embedding path. The API does not accept user-supplied model checkpoints or expose Trainer checkpoint loading, but uploaded documents still feed embedding text and require strict parser and content-size controls.

Not passed:

- Raw `pip-audit` without the gate.
- Transformers 5.x upgrade; not attempted in mainline because it needs a separate BGE/RAG compatibility branch.
