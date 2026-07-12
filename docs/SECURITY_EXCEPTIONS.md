# Security Exceptions

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
