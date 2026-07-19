# Testing
## v1.8.9 Test Notes

- Smoke: `python apps/api/scripts/smoke_minimal.py --expected-version v1.8.9 --expected-model "meizhaiseek 2.0"`.
- Pool metrics exporter: `python apps/api/scripts/export_pool_metrics.py --metrics-url http://127.0.0.1/metrics`.
- Browser matrix: `cd apps/web && npm.cmd run e2e:agent -- --project=chrome`; set `MEIZHAISEEK_E2E_RUN_VIDEO=1` only when the local video Agent and test video are available.
- Capacity: run 100 users first; run 200 users only after browser matrix, multi-instance SSE, pool metrics, Docker health, queue depth, and quality gates pass.
- SQL safety: `.venv\Scripts\python.exe apps/api/scripts/scan_sql_safety.py --json-report --fail-on-new --baseline docs/sql_safety_baseline_v186.json`; v1.8.9 result was `passed`, baseline `31`, high-risk `0`.
- Dependency audit gate: raw `.venv\Scripts\python.exe -m pip_audit --format json` remains `failed` with 4 documented `transformers 4.57.6` advisories; `.venv\Scripts\python.exe apps/api/scripts/check_pip_audit_report.py <raw-json>` passed.
- Typing: `.venv\Scripts\python.exe -m mypy apps/api` passed after adding a targeted `pydantic.*` `follow_imports = "normal"` override.

## v1.8.7 Final Validation - 2026-07-17

Executed and passed:

- `python -m compileall apps/api`.
- `.venv\Scripts\python.exe -m ruff check apps/api`.
- `.venv\Scripts\python.exe -m mypy apps/api`.
- `python -m unittest discover -s apps/api/tests`.
- `.venv\Scripts\python.exe -m pytest apps/api/tests`.
- `.venv\Scripts\python.exe -m bandit --severity-level medium -r apps/api`.
- `cd apps/web; npm.cmd ci; npm.cmd run build`.
- `npm.cmd run e2e:agent -- --project=chrome` for the core `/agent` browser smoke.
- `apps/api/scripts/check_pip_audit_report.py` against the raw v1.8.7 pip-audit JSON.

Executed and not passed:

- Raw `pip-audit` remains `failed` with 5 documented accepted-risk advisories in `setuptools 81.0.0` and `transformers 4.57.6`.
- Full browser Agent matrix remains incomplete because video artifact downloads, cancel, retry, and browser SSE terminal-close timing were not executed.

Executed acceptance:

- Knowledge queue: `passed`, 5 documents, 55 chunks, reindex completed, top-k returned 5 sources.
- MinIO artifact storage: `passed`, including 10MB and 100MB streaming, TTL expiry, cross-user denial, path traversal denial, checksum, content-type, Chinese filename, and JSON/Excel/evidence downloads.
- pgvector: `passed`, including dry-run, execute, verify, controlled resume, repeat execute/verify, orphan cleanup, and exact SQLite/pgvector top5 match.
- 100 users, 15 minutes: `passed`, 0 failures, aggregate p95 140ms, p99 310ms, final queue depth 0.

Not executed:

- 200/300/500-user capacity tests.
- Full browser video/download/cancel/retry matrix.

## v1.8.4 Validation Gates

Use `not_run`, `failed`, and `passed` only. Older v1.8.3 results are historical evidence and must not be copied as v1.8.4 pass results.

- Backend gates: compileall, ruff, mypy, unittest, pytest.
- Security gates: Bandit medium+ and pip-audit with only documented exceptions.
- Frontend gate: `npm.cmd ci` and `npm.cmd run build`.
- P0-P4 operational gates are documented in the `docs/V184_*` files.

## meizhaiseek v1.8.3 P0/P1 update, 2026-07-12

Executed and passed:

- `python -m compileall apps/api`: passed.
- `.venv\Scripts\python.exe -m ruff check apps/api`: passed.
- `.venv\Scripts\python.exe -m mypy apps/api`: passed for 182 source files after adding the Dataset queue test.
- `python -m unittest discover -s apps/api/tests`: 71 tests OK.
- `python -m pytest apps/api/tests`: 71 passed, 2 skipped.
- `.venv\Scripts\python.exe -m bandit --severity-level medium -r apps/api`: passed; High=0, Medium=0.
- `.venv\Scripts\python.exe -m pip_audit --ignore-vuln PYSEC-2025-217 --ignore-vuln GHSA-69w3-r845-3855 --ignore-vuln GHSA-29pf-2h5f-8g72`: passed with 3 ignored advisories.
- BGE-small-zh smoke: passed, model loaded, embedding dimension 512.
- pgvector non-empty migration validation: passed with 5 documents, 60 chunks, dry-run/execute/verify/resume, and top-k search.

Executed and not passed:

- Raw `.venv\Scripts\python.exe -m pip_audit`: failed with the three documented `transformers 4.57.6` advisories.
- First 100-user Locust attempt: not passed because the runtime Locust environment script could not be loaded by PowerShell execution policy and the run fell back to default admin credentials.

Executed performance smoke:

- 100 users, 15 minutes, 140 temporary operator accounts, host `http://127.0.0.1`.
- Result: 0 failures, aggregate p95 110ms, `/api/agent-runs` submit p95 370ms, `/api/agents` p95 64ms, login p95 260ms.
- Queue depth recovered to 0 for `general`, `video`, `dataset`, `knowledge`, and `blueprint`.

Not executed:

- P2 Redis pause/recovery full acceptance.
- P2 worker crash/restart and 50 video queue acceptance.
- P2 MinIO permissions/TTL/streaming acceptance.
- P3 200/300/500 user tests.

## meizhaiseek v1.8.2 P0/P1 update, 2026-07-10

Executed and passed:

- `python -m compileall apps/api`: passed.
- `.venv\Scripts\python.exe -m ruff check apps/api`: passed.
- `.venv\Scripts\python.exe -m mypy apps/api`: passed for 181 source files.
- `.venv\Scripts\python.exe -m mypy apps/api/services apps/api/tasks apps/api/storage apps/api/rag apps/api/db apps/api/routers apps/api/tests`: passed for 151 source files.
- `python -m unittest discover -s apps/api/tests`: 59 tests OK.
- `python -m pytest apps/api/tests`: 59 passed, 2 skipped.
- `.venv\Scripts\python.exe -m bandit --severity-level medium -r apps/api`: passed; High=0, Medium=0.
- `.venv\Scripts\python.exe -m pip_audit --ignore-vuln PYSEC-2025-217 --ignore-vuln GHSA-69w3-r845-3855 --ignore-vuln GHSA-29pf-2h5f-8g72`: passed with 3 ignored advisories.

Executed and not passed:

- Raw `.venv\Scripts\python.exe -m pip_audit`: failed with the three documented `transformers 4.57.6` advisories.

Executed performance smoke:

- 100 users, 15 minutes, 140 temporary operator accounts, host `http://127.0.0.1`.
- Result: 0 failures, aggregate p95 120ms, `/api/agent-runs` p95 130ms, `/api/agents` p95 27ms, login p95 210ms.
- Queue depth recovered to 0 after scaling `worker-general` to 4.

Not executed:

- P2 worker crash/restart.
- 50 video queue acceptance.
- P3 200/300/500 user tests.
## 本地测试

```powershell
python -m compileall apps/api
python -m unittest discover -s apps/api/tests
cd apps/web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run build
cd ..\..
python apps/api/scripts/smoke_minimal.py
```

## 视频 Agent E2E

```powershell
python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent
```

可配置变量：

- `API_BASE_URL`
- `SMOKE_ADMIN_USERNAME`
- `SMOKE_ADMIN_PASSWORD`
- `VIDEO_AGENT_BASE_URL`
- `VIDEO_AGENT_TEST_VIDEO`
- `VIDEO_AGENT_TEST_OUTPUT_DIR`

## 单元测试说明

`apps/api/tests` 使用 Python 标准 `unittest`。测试默认使用临时 SQLite 路径，不依赖 DeepSeek、BGE 模型或 8001 服务。

## 常见失败原因

- 后端未启动。
- 本地管理员密码未通过环境变量传入。
- 8001 未启动但指定了 `--require-video-agent`。
- 前端 build 未设置 `NEXT_PUBLIC_API_BASE_URL`。

## v1.7.2 验证命令

- `python -m compileall apps/api`
- `python -m unittest discover -s apps/api/tests`
- `python -m pytest apps/api/tests`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build`
- `python apps/api/scripts/smoke_minimal.py`

默认测试使用临时 SQLite，不依赖 8001、DeepSeek 或 BGE。真实视频 E2E 仍通过 `python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent` 手动执行。

## v1.8 验证命令

P1/P2/P3 本地回归：

- `python -m compileall apps/api`
- `python -m unittest discover -s apps/api/tests`
- `python -m pytest apps/api/tests`
- `python apps/api/scripts/migrate_sqlite_to_postgres.py --dry-run --json-report`
- `python apps/api/scripts/migrate_sqlite_to_postgres.py --verify`
- `cd apps/web; $env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'; npm.cmd run build`
- `docker compose -f docker-compose.prod.yml config`

PostgreSQL/RQ/Redis 生产链路需要本机或 CI 提供 PostgreSQL、Redis 和 Docker daemon 后再执行：

- `alembic upgrade head`
- Redis Pub/Sub integration：API A 创建 run，worker 更新 run，API B SSE 接收轻量事件后重新读 DB summary。
- Worker tests：retry limits、timeout、cancellation、duplicate enqueue idempotency、zombie recovery。
- Artifact tests：local compatibility、S3/mock provider、ownership、checksum、streaming download。

Locust 基线：

```powershell
locust -f load_tests/locustfile.py --headless -u 20 -r 5 -t 2m --host http://127.0.0.1:8000
```

100 用户以上请使用临时账号池，避免单一 admin username 触发登录限流：

```powershell
$env:LOCUST_USER_PREFIX='loadtest_'
$env:LOCUST_USER_COUNT='200'
$env:LOCUST_ADMIN_PASSWORD='<temporary-load-test-password>'
locust -f load_tests/locustfile.py --headless -u 100 -r 10 -t 5m --host http://127.0.0.1
```

2026-07-05 真实结果：20 用户通过；100 用户 0% 错误但 p95 延迟未达目标；500 用户未执行。

500 用户只在硬件、PostgreSQL、Redis、worker 和外部 mock 全部就绪时执行。未执行时必须在 `docs/CAPACITY_REPORT_V18.md` 明确标注，不写假结果。

## meizhaiseek v1.7.2

v1.7.2 focuses on architecture stabilization after the 2026-07-03 evaluation: Blueprint release E2E coverage, wider auth/conversation/task tests, Blueprint Store splitting, legacy JSON fallback retirement diagnostics, production Docker build/start, Agent Run SSE tests, async SQLite read wrappers, frontend API module compatibility split, methodology drag ordering, Registry/Blueprint reconciliation, and the Agent Run Event Hub. Existing Agent, Workflow, Connector, APP SQLite, RAG SQLite, Dataset, QA/RAG, Debug Payload, and video breakdown execution models are unchanged.

## meizhaiseek v1.8.2 P1

Final executed commands on 2026-07-06:

- `python -m compileall apps/api`: passed.
- `python -m unittest discover -s apps/api/tests`: 53 tests OK.
- `python -m pytest apps/api/tests`: 53 passed, 2 skipped, 2 warnings.
- `.venv\Scripts\python.exe -m ruff check apps/api`: passed.
- `.venv\Scripts\python.exe -m mypy`: passed for the scoped production modules in `pyproject.toml`.
- `.venv\Scripts\python.exe -m bandit -r apps/api -f json -o apps/api/runtime/logs/bandit-v182.json`: executed; High=0, Medium=0, Low=33.
- `.venv\Scripts\python.exe apps/api/scripts/check_bandit_report.py apps/api/runtime/logs/bandit-v182.json`: passed.
- `.venv\Scripts\python.exe -m pip_audit -f json -o apps/api/runtime/logs/pip-audit-v182.json`: 未通过 raw scan, 3 transformers advisories.
- `.venv\Scripts\python.exe apps/api/scripts/check_pip_audit_report.py apps/api/runtime/logs/pip-audit-v182.json`: passed with exact temporary exceptions.
- `cd apps/web; $env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'; npm.cmd run build`: passed.
- 100-user Locust 10m with 120 temporary operator accounts: passed minimum gate, 0 failures, aggregate p95 160ms.

P1 not fully ideal:

- Agent submit p95 was 600ms, so the <=500ms priority target is 未通过.
- sentence-transformers 5.x / transformers 5.x upgrade smoke is 未执行.
- P2/P3 tests are 未执行 in this section.

P2 optional integration markers:

- `apps/api/tests/integration/test_distributed_sse_recovery.py`
- `apps/api/tests/integration/test_worker_recovery.py`

These are skipped by default. Set `RUN_DISTRIBUTED_ACCEPTANCE_TESTS=1` only when a live Docker production topology and the required fault-injection setup are available.

## meizhaiseek v1.8.2 P1 update, 2026-07-07

- `python -m compileall apps/api`: passed.
- `python -m unittest discover -s apps/api/tests`: 54 tests OK.
- `python -m pytest apps/api/tests`: 54 passed, 2 skipped.
- `.venv\Scripts\python.exe -m ruff check apps/api`: passed.
- `.venv\Scripts\python.exe -m mypy`: passed for 33 scoped source files.
- `.venv\Scripts\python.exe -m bandit -r apps/api -f json -o apps/api/runtime/logs/bandit-v182-p1.json`: executed; High=0, Medium=0, Low=35.
- `.venv\Scripts\python.exe apps/api/scripts/check_bandit_report.py apps/api/runtime/logs/bandit-v182-p1.json`: passed.
- `.venv\Scripts\python.exe -m pip_audit -f json -o apps/api/runtime/logs/pip-audit-v182-p1.json`: raw scan still reports 3 transformers advisories.
- `.venv\Scripts\python.exe apps/api/scripts/check_pip_audit_report.py apps/api/runtime/logs/pip-audit-v182-p1.json`: passed with documented temporary exceptions.
- `python apps/api/scripts/verify_schema_parity.py --json-report`: passed.
- `python apps/api/scripts/migrate_rag_sqlite_to_pgvector.py --dry-run --json-report`: passed on current empty SQLite RAG source.
- `cd apps/web; $env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'; npm.cmd ci; npm.cmd run build`: passed.

## meizhaiseek v1.8.6 SQL Safety

- `python apps/api/scripts/scan_sql_safety.py --json-report`: executed.
- `python apps/api/scripts/scan_sql_safety.py --json-report --fail-on-new --baseline docs/sql_safety_baseline_v186.json`: passed.
- CI runs the same baseline gate after Bandit.
- Baseline is 31 findings; high-risk findings are 0 after v1.8.6 helper guard fixes.
