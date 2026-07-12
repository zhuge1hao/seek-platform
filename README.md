# meizhaiseek-platform

## Latest v1.8.3 Runtime Note

Branch: `stabilization/v1.8.3`.

`meizhaiseek v1.8.3` is a production-acceptance hardening release on top of v1.8.2. It keeps `meizhaiseek 2.0`, preserves the existing product navigation, and focuses on full type gates, queue closure, pgvector validation, and honest P2/P3 acceptance tracking. It does not add new business agents.

## Latest v1.8.2 Runtime Note

As of 2026-07-07, the local Docker production topology on branch `stabilization/v1.8.2` has been recovered and started:

- PostgreSQL/pgvector, Redis, MinIO, API, Web, Nginx, `worker-general`, and `worker-video` are running.
- APP SQLite data was restored into PostgreSQL and verified.
- RAG pgvector migration tooling ran successfully with zero source RAG documents/chunks.
- Login, runtime health, Agent Run enqueue, and SSE smoke passed.
- `/health/ready` is currently degraded because the local admin password was restored to the legacy default at user request.
- Full P2 distributed acceptance and P3 200/300/500-user capacity validation remain not executed.

meizhaiseek-platform 是面向电商经营场景的本地轻量 AI 工作台。当前版本为 **meizhaiseek v1.8**，包含 Next.js 前端、FastAPI 后端、APP SQLite、RAG SQLite、AI 对话、AI 智能体、Dataset、Connector、Debug Payload、后台账号管理、视频拆解智能体产物闭环，以及智能体蓝图与方法论配置中心。

v1.8 增加 500 用户并发扩展基础：PostgreSQL/Alembic 生产路径、Redis/RQ 队列、分布式 Agent Run 事件、artifact storage facade、RAG provider facade、request id/metrics、Locust 基线脚本和生产部署文档。本地开发默认仍使用 SQLite、memory events、inline queue 和 local artifacts。

模型展示名保持为 **meizhaiseek 2.0**。

## 快速启动

推荐在项目根目录运行：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

默认地址：

- Web: http://localhost:3000
- API: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- 日志目录: `apps/api/runtime/logs/`

也可以分别启动：

```powershell
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
cd apps/web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run dev
```

## 配置

复制 `.env.example` 后按本地环境调整。生产部署前请设置：

- `AUTH_TOKEN_SECRET`
- `MEIZHAISEEK_ADMIN_INITIAL_PASSWORD`
- `NEXT_PUBLIC_API_BASE_URL`

如果未设置 `AUTH_TOKEN_SECRET`，后端会在 `apps/api/runtime/app/generated_secrets.json` 生成本地 secret。该文件不应提交到 Git。

`APP_LEGACY_JSON_FALLBACK=false` 是默认推荐值。只有紧急恢复旧 JSON 数据时才临时设为 `true`。

v1.8 新增生产扩展配置：

- `APP_DB_BACKEND=sqlite|postgres`
- `APP_DATABASE_URL`
- `CACHE_BACKEND=memory|redis`
- `EVENT_BACKEND=memory|redis`
- `TASK_QUEUE_BACKEND=inline|redis`
- `REDIS_URL`
- `ARTIFACT_STORAGE_BACKEND=local|local_shared|s3`
- `RAG_BACKEND=sqlite|pgvector`

## 测试

```powershell
python -m compileall apps/api
python -m unittest discover -s apps/api/tests
python -m pytest apps/api/tests
cd apps/web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run build
cd ..\..
python apps/api/scripts/smoke_minimal.py
```

如本地视频拆解 Agent 已启动，可运行：

```powershell
python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent
```

## Docker

开发模式：

```powershell
docker compose up --build
```

生产模式：

```powershell
docker compose -f docker-compose.prod.yml up --build -d
```

Docker 内访问宿主机视频 Agent 时，Connector Base URL 使用：

```text
http://host.docker.internal:8001
```

## 运行数据

- APP SQLite: `apps/api/runtime/app/meizhaiseek.sqlite3`
- RAG SQLite: `apps/api/runtime/rag/rag.sqlite3`
- 上传文件: `apps/api/uploads/`
- 日志: `apps/api/runtime/logs/`

这些运行时文件不应提交到 Git。


## meizhaiseek v1.8

v1.8 prepares the platform for the 500-user production architecture without removing the local SQLite path. The production recommendation is PostgreSQL + Redis + RQ workers + distributed SSE wakeups + shared artifact storage. The current implementation includes the migration foundation, queue/event/storage/provider abstractions, health/readiness endpoints, request/metrics middleware, Docker production topology, and Locust scenarios. Full 500-user load results are not claimed unless `docs/CAPACITY_REPORT_V18.md` records an actual successful run.

## meizhaiseek v1.7.2

v1.7.2 focuses on architecture stabilization after the 2026-07-03 evaluation: Blueprint release E2E coverage, wider auth/conversation/task tests, Blueprint Store splitting, legacy JSON fallback retirement diagnostics, production Docker build/start, Agent Run SSE tests, async SQLite read wrappers, frontend API module compatibility split, methodology drag ordering, Registry/Blueprint reconciliation, and the Agent Run Event Hub. Existing Agent, Workflow, Connector, APP SQLite, RAG SQLite, Dataset, QA/RAG, Debug Payload, and video breakdown execution models are unchanged.
