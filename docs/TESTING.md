# Testing

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
