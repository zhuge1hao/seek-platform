# Security Exceptions
## v1.8.9 Recheck Status

Raw pip-audit is `failed` for v1.8.9 with 4 known vulnerabilities in 1 package after local environment refresh. The accepted-risk gate is `passed` with only exact, unexpired `transformers 4.57.6` advisories. The new `torch 2.12.1` / `GHSA-rrmf-rvhw-rf47` finding was not accepted as risk; it was cleared by upgrading the local `.venv` to `torch 2.13.0` and `setuptools 83.0.0`, matching the already-fixed production API image versions.

Executed:

- Ran raw `.venv\Scripts\python.exe -m pip_audit --format json > apps/api/runtime/logs/pip_audit_v189_raw.json`: failed, 4 advisories in 1 package.
- Ran `.venv\Scripts\python.exe apps/api/scripts/check_pip_audit_report.py apps/api/runtime/logs/pip_audit_v189_raw.json`: passed.
- Ran local `.venv\Scripts\python.exe -m pip install --dry-run torch==2.13.0 setuptools==83.0.0`: passed.
- Upgraded local `.venv` to `torch 2.13.0` and `setuptools 83.0.0`; `pip check` passed.
- Confirmed production API container uses `torch 2.13.0`, `setuptools 83.0.0`, `sentence-transformers 3.3.1`, and `transformers 4.57.6`; production `pip check` passed.
- Ran BGE smoke after local upgrade: `success bge-small-zh 512`.

## v1.8.7 Recheck - 2026-07-17

Status: raw `pip-audit` remains not clean in the local `.venv`; the exception gate passes with only exact, unexpired advisories.

Executed:

- Ran raw `.venv\Scripts\python.exe -m pip_audit --format json > apps/api/runtime/logs/pip_audit_v187_raw.json`.
- Raw result: 5 advisories in 2 packages.
- Ran `apps/api/scripts/check_pip_audit_report.py apps/api/runtime/logs/pip_audit_v187_raw.json`: passed.
- Ran local `.venv\Scripts\python.exe -m pip check`: passed.
- Ran production container `python -m pip check`: passed.
- Confirmed production API container uses `setuptools 83.0.0`, while the local `.venv` still has `setuptools 81.0.0`.
- Checked current package sources on 2026-07-17: `setuptools 83.0.0` is the current fix path; Sentence Transformers 5.x has a Transformers 5 support path, but no production upgrade was attempted without a full BGE/RAG smoke.

Accepted risk:

| Advisory ID | Package | Current version | Fix version | Scope | Reason | Review date | Expiry date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `PYSEC-2026-3447` | `setuptools` | `81.0.0` in local `.venv`; `83.0.0` in production API container | `83.0.0` | Local/dev audit environment only after v1.8.7 production image check | Production image no longer shows `setuptools 81.0.0`; local upgrade remains tied to the local `torch 2.12.1` constraint and must be rechecked with environment refresh. | 2026-07-17 | 2026-08-17 |
| `PYSEC-2025-217` | `transformers` | `4.57.6` | none listed | Local BGE-small-zh embedding dependency path | Production API does not expose Trainer checkpoint loading or user-supplied model checkpoint execution. | 2026-07-17 | 2026-09-17 |
| `PYSEC-2026-2290` | `transformers` | `4.57.6` | none listed | Local BGE-small-zh embedding dependency path | Same restricted embedding scope; upgrade requires BGE/RAG smoke proof. | 2026-07-17 | 2026-09-17 |
| `PYSEC-2026-2288` | `transformers` | `4.57.6` | `5.0.0` | Local BGE-small-zh embedding dependency path | Fix requires Transformers 5.x and compatible `sentence-transformers`; not upgraded without full embedding/RAG smoke. | 2026-07-17 | 2026-09-17 |
| `PYSEC-2026-2289` | `transformers` | `4.57.6` | `5.3.0` | Local BGE-small-zh embedding dependency path | Fix requires Transformers 5.3+ and compatible `sentence-transformers`; not upgraded without full embedding/RAG smoke. | 2026-07-17 | 2026-09-17 |

Not passed:

- Raw `pip-audit`.
- Transformers 5.x upgrade.

## v1.8.6 Review Update - 2026-07-17

Status: raw `pip-audit` is not clean. The gate passes only if the exact package/advisory exceptions below are present and not expired.

Executed:

- Ran raw `.venv\Scripts\python.exe -m pip_audit --format json`.
- Observed 5 advisories: one `setuptools 81.0.0` advisory and four `transformers 4.57.6` advisories.
- Attempted `setuptools==83.0.0`; raw audit removed the setuptools advisory, but `pip check` failed because `torch 2.12.1` requires `setuptools<82`.
- Reverted to `setuptools==81.0.0`; `pip check` passed.
- Updated CI to save raw pip-audit JSON and run `apps/api/scripts/check_pip_audit_report.py`.
- Checked package index: `sentence-transformers` latest observed `5.6.0`; `transformers` latest observed `5.14.1`.
- Ran the v1.8.6 gate script against the raw JSON report: passed with only the exact package/advisory exceptions listed below.

Accepted risk:

| Advisory ID | Package | Current version | Fix version | Scope | Reason | Review date | Expiry date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `PYSEC-2026-3447` | `setuptools` | `81.0.0` | `83.0.0` | Local/dev and build audit environment | Direct upgrade currently violates the installed `torch 2.12.1` requirement `setuptools<82`; this must be revisited with the torch/embedding dependency upgrade. | 2026-08-17 | 2026-08-17 |
| `PYSEC-2025-217` | `transformers` | `4.57.6` | none listed | Local BGE-small-zh embedding dependency path | Production API does not expose Trainer checkpoint loading or user-supplied model checkpoint execution. | 2026-08-17 | 2026-09-17 |
| `PYSEC-2026-2290` | `transformers` | `4.57.6` | none listed | Local BGE-small-zh embedding dependency path | Same restricted embedding scope; upgrade requires BGE/RAG smoke proof. | 2026-08-17 | 2026-09-17 |
| `PYSEC-2026-2288` | `transformers` | `4.57.6` | `5.0.0` | Local BGE-small-zh embedding dependency path | Fix requires Transformers 5.x and compatible `sentence-transformers`; not upgraded without full embedding/RAG smoke. | 2026-08-17 | 2026-09-17 |
| `PYSEC-2026-2289` | `transformers` | `4.57.6` | `5.3.0` | Local BGE-small-zh embedding dependency path | Fix requires Transformers 5.3+ and compatible `sentence-transformers`; not upgraded without full embedding/RAG smoke. | 2026-08-17 | 2026-09-17 |

Not passed:

- Raw `pip-audit` without exception gate.
- Safe setuptools upgrade, because `pip check` failed with current torch metadata.
- Transformers 5.x upgrade, because the required BGE/RAG smoke was not executed in this phase.

## v1.8.3 Review Update - 2026-07-12

Status: reviewed again for v1.8.3. Raw `pip-audit` remains not clean; the security gate remains clean only with the three exact documented advisory exceptions below.

Executed:

- Checked local packages: `sentence-transformers==3.3.1`, `transformers==4.57.6`, `torch==2.12.1`.
- Checked upstream release information: `sentence-transformers` 5.x has a Transformers 5 support path, and the affected `transformers` advisories have fixed-version paths in 5.x.
- Ran BGE-small-zh smoke on the current stack: model loaded, embedding dimension was 512.
- Ran non-empty pgvector migration validation on isolated test data: 5 documents, 60 chunks, 512-dimensional embeddings, dry-run/execute/verify/resume all passed.
- Ran raw `pip-audit`: failed with the three `transformers 4.57.6` advisories.
- Ran `pip-audit` with exact exceptions: passed with 3 ignored advisories.

Accepted risk:

- `PYSEC-2025-217`, `GHSA-69w3-r845-3855`, and `GHSA-29pf-2h5f-8g72` remain accepted only for the local BGE-small-zh embedding dependency path.
- The production API does not accept user-uploaded model checkpoints and does not expose Trainer checkpoint loading.
- Review date: 2026-08-12.
- Expiry date: 2026-09-12.

Not executed:

- Production dependency upgrade to `sentence-transformers` 5.x / `transformers` 5.x.
- Full post-upgrade BGE/RAG regression on the upgraded dependency stack.

Not passed:

- Raw `pip-audit` without exact documented exceptions.

## v1.8.2 Review Update - 2026-07-10

Status: reviewed again. Raw `pip-audit` is still not clean; the CI gate remains clean only when the three exact advisory exceptions below are supplied.

Executed:

- Checked current local packages: `sentence-transformers==3.3.1`, `transformers==4.57.6`, `torch==2.12.1`.
- Checked current PyPI / upstream release information. `sentence-transformers` 5.x now has a Transformers v5 support path, and `transformers` 5.x has fixes for at least two of the three advisories.
- Ran BGE-small-zh smoke on the current stack: model loaded, embedding dimension was 512, SQLite RAG retrieval returned the inserted test chunk.
- Ran pgvector smoke on the current stack: model loaded, embedding dimension was 512, pgvector retrieval returned the inserted test chunk, and the temporary pgvector document was deleted.
- Ran raw pip-audit: failed with the three `transformers 4.57.6` advisories.
- Ran pip-audit with exact exceptions: passed with 3 ignored advisories.

Accepted risk:

- `PYSEC-2025-217`, `GHSA-69w3-r845-3855`, and `GHSA-29pf-2h5f-8g72` remain accepted only for the local BGE-small-zh embedding path.
- The core API does not accept user-uploaded model checkpoints and does not expose Trainer checkpoint loading.
- Review date remains 2026-08-06.
- Expiry date remains 2026-09-06.

Not executed:

- Upgrade to `sentence-transformers` 5.x / `transformers` 5.x in the production dependency set.
- Full post-upgrade RAG regression.

Not passed:

- Raw `pip-audit` without exact documented exceptions.

## v1.8.2 Temporary Dependency Exceptions

Status: 已审查，带到期日期。新增 pip-audit 漏洞不得自动放行。

| Advisory ID | Package | Current version | Scope | Reason | Review date | Expiry date |
| --- | --- | --- | --- | --- | --- | --- |
| PYSEC-2025-217 | transformers | 4.57.6 | Optional local RAG embedding worker dependency | Fix path requires transformers 5.x. Current BGE-small-zh path is pinned through sentence-transformers 3.3.1; upgrading without a full embedding smoke risks breaking RAG. No untrusted checkpoint conversion is exposed through core API. | 2026-08-06 | 2026-09-06 |
| GHSA-69w3-r845-3855 | transformers | 4.57.6 | Optional local RAG embedding worker dependency | Affects Trainer RNG state loading. Production API does not expose Trainer or accept user-supplied trainer checkpoints. | 2026-08-06 | 2026-09-06 |
| GHSA-29pf-2h5f-8g72 | transformers | 4.57.6 | Optional local RAG embedding worker dependency | Requires malicious model/config loading. Current configured model is local BGE-small-zh; model uploads are not accepted from ordinary users. | 2026-08-06 | 2026-09-06 |

未执行：sentence-transformers 5.x / transformers 5.3.0 upgrade smoke。
未通过：raw `pip-audit` without approved exception handling still reports the three advisories above.
