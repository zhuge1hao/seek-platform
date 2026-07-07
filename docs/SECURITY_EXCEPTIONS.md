# Security Exceptions

## v1.8.2 Temporary Dependency Exceptions

Status: 已审查，带到期日期。新增 pip-audit 漏洞不得自动放行。

| Advisory ID | Package | Current version | Scope | Reason | Review date |
| --- | --- | --- | --- | --- | --- |
| PYSEC-2025-217 | transformers | 4.57.6 | Optional local RAG embedding worker dependency | Fix path requires transformers 5.x. Current BGE-small-zh path is pinned through sentence-transformers 3.3.1; upgrading without a full embedding smoke risks breaking RAG. No untrusted checkpoint conversion is exposed through core API. | 2026-08-06 |
| GHSA-69w3-r845-3855 | transformers | 4.57.6 | Optional local RAG embedding worker dependency | Affects Trainer RNG state loading. Production API does not expose Trainer or accept user-supplied trainer checkpoints. | 2026-08-06 |
| GHSA-29pf-2h5f-8g72 | transformers | 4.57.6 | Optional local RAG embedding worker dependency | Requires malicious model/config loading. Current configured model is local BGE-small-zh; model uploads are not accepted from ordinary users. | 2026-08-06 |

未执行：sentence-transformers 5.x / transformers 5.3.0 upgrade smoke。
未通过：raw `pip-audit` without approved exception handling still reports the three advisories above.
