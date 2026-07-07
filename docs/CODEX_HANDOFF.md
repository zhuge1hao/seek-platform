# Codex Handoff

## v1.8.2 Docker Recovery Handoff - 2026-07-07

- Branch: `stabilization/v1.8.2`.
- Latest pushed code commit before this doc update: `c4f8c4114d82e6de513ce55b1faa7c0f979094ec`.
- Runtime version: `meizhaiseek v1.8.2`; model display name: `meizhaiseek 2.0`.
- Docker Desktop Linux Engine was restored without unregistering WSL, pruning Docker data, resetting Docker Desktop, or deleting the relocated VHDX.
- Docker VHDX link is valid: `C:\Users\Administrator\AppData\Local\Docker\wsl\disk\docker_data.vhdx` -> `E:\USE\Docker\docker-desktop-disk\docker_data.vhdx`.
- Production compose was rebuilt from empty Docker resources and is running PostgreSQL, Redis, MinIO, API, Web, Nginx, `worker-general`, and `worker-video`.
- Current compose does not define separate `worker-dataset`, `worker-knowledge`, or `worker-blueprint`; queue-specific P2 acceptance for those queues remains not executed.
- Alembic current: `20260705_v18_initial (head)`.
- Host SQLite APP data was backed up under runtime and restored into PostgreSQL. Verify passed for the migration script.
- pgvector extension is enabled. RAG SQLite-to-pgvector dry-run/execute/verify passed with zero source documents/chunks, so this is an empty migration verification, not a full RAG data migration.
- `/health`, `/health/live`, `/metrics`, login, runtime health, and a header-auth SSE smoke passed.
- Local admin password was restored to the legacy default at the user's request. Therefore `/health/ready` is currently `degraded` by design with `default_admin_password_detected=true`.
- Do not claim production readiness is fully green while the default admin password is active.
- Protected worktree rule still applies: do not stage or modify `ARCHITECTURE_EVALUATION_REPORT.md`; it remains a user-owned dirty file.

## v1.8.2 Handoff - 2026-07-06

- Current code/runtime version: `meizhaiseek v1.8.2`.
- Model display name: `meizhaiseek 2.0`.
- Branch: `main`.
- Last pushed commit is still `cae7884 refactor: stabilize architecture P1-P3 for v1.7.2`.
- Worktree is dirty. Do not use `git add .` or `git add -A`.
- Do not stage `.env`, runtime/logs/uploads/models/node_modules, local Locust CSV/log artifacts, or `ARCHITECTURE_EVALUATION_REPORT.md`.
- `ARCHITECTURE_EVALUATION_REPORT.md` is a protected user change; do not fix its known line 793 trailing whitespace.

P1 status:

- Passed minimum quality/capacity gates.
- `compileall`: passed.
- `unittest`: 53 OK.
- `pytest`: 53 passed, 2 skipped, 2 warnings.
- `ruff`: passed.
- scoped `mypy`: passed.
- Bandit: High=0, Medium=0, Low=33.
- pip-audit raw scan: 未通过 for three `transformers 4.57.6` advisories; exact exceptions documented.
- Frontend build: passed.
- 100-user 10m operator-pool Locust: 0 failures, aggregate p95 160ms.
- Agent submit p95: 600ms, so <=500ms priority target is 未通过.

P2 status:

- Redis pause/recovery SSE with API A/API B: passed.
- Runtime health `multi_instance_sse_verified=passed`.
- Controlled zombie maintenance repair: passed after terminal-update protection fix.
- Full worker crash/restart/retry: 未执行.
- 50 video queue, Dataset queue, Document ingest queue, Blueprint queue, full MinIO, pgvector migration, schema parity: 未执行.

P3 status:

- 未执行. Do not run or claim 200/300/500 user validation until P2 is complete.

## 项目名称与当前版本

- 项目：meizhaiseek-platform
- 当前版本：meizhaiseek v1.8.1
- 版本名：安全加固、100 用户性能收敛与分布式链路验收
- 模型名：meizhaiseek 2.0
- 仓库：https://github.com/zhuge1hao/seek-platform.git
- 本地路径：`E:\USE\codexhome\agents-cowork\meizhaiseek-platform`
- 当前分支：main
- 最近已推送提交：`cae7884 refactor: stabilize architecture P1-P3 for v1.7.2`
- 当前状态：工作区仍未提交，包含 v1.8 基础改动、v1.8.1 安全/性能改动、文档改动和用户既有 `ARCHITECTURE_EVALUATION_REPORT.md` 改动。不要裸 `git add .`。

## 当前项目目标

meizhaiseek-platform 是本地/私有化 AI 工作台，服务电商经营、内容拆解、QA/RAG、Dataset、Blueprint 和视频脚本拆解。当前目标不是新增业务智能体，而是把 v1.8 分布式生产路径补稳到 v1.8.1：安全前置项、100 用户性能收敛、分布式链路验收，并继续保护 `/agent` 真实任务和聊天持久化。

## 技术栈与启动方式

- 前端：Next.js 14 App Router、React 18、TypeScript、Tailwind、SWR、lucide-react。
- 后端：FastAPI、Uvicorn、Pydantic、sqlite3、psycopg、SQLAlchemy async、asyncpg、Alembic、Redis、RQ、Prometheus metrics。
- 默认开发存储：APP SQLite `apps/api/runtime/app/meizhaiseek.sqlite3`，RAG SQLite `apps/api/runtime/rag/rag.sqlite3`。
- 生产推荐路径：PostgreSQL + Redis/RQ + Redis events + MinIO/S3 + pgvector。
- 本地视频 Agent：`http://127.0.0.1:8001`；Docker 内访问宿主机使用 `http://host.docker.internal:8001`。

开发启动：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

后端单启：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\api
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

前端单启：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run dev -- -p 3000
```

生产拓扑：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
docker compose -f docker-compose.prod.yml up -d --build --scale worker-general=4 --scale worker-video=2
docker compose -f docker-compose.prod.yml ps
```

## 关键目录结构

```text
apps/api/main.py                         FastAPI app, health, metrics, startup
apps/api/routers                         HTTP API routes
apps/api/schemas                         Pydantic request/response schemas
apps/api/services                        stores, auth, security, tasks, connectors, QA/RAG, Blueprint
apps/api/db                              SQLAlchemy async, Alembic, PostgreSQL schema
apps/api/tasks                           inline/RQ queue facade and task entry points
apps/api/workers                         RQ worker entry
apps/api/storage                         artifact storage providers: local/local_shared/s3
apps/api/rag                             RAG providers: sqlite/pgvector
apps/api/scripts                         smoke, migration, verification scripts
apps/api/tests                           unittest/pytest tests
apps/api/runtime                         local runtime data, never commit
apps/api/uploads                         uploaded files, never commit
apps/web/src/app                         Next.js pages
apps/web/src/components                  Agent, Chat, Dataset, Admin, Blueprint UI
apps/web/src/hooks                       SWR, SSE, polling hooks
apps/web/src/lib                         auth, api client, registry, helpers
load_tests                               Locust scripts
docs                                    product, API, testing, scaling, handoff docs
```

## 已完成版本记录

### v1.8.1

- 安全：生产不再回退固定 JWT secret；本地缺 secret 时生成 runtime secret；生产禁止 `admin123` 初始管理员弱密码；runtime health 只显示 secret 状态。
- 安全：`table_count()` 增加表名白名单；CLI Connector 使用 `shell=False` 并拒绝 shell metacharacters；静默异常改为脱敏日志；迁移/文件 ID 从 SHA1 改 SHA256。
- 依赖：FastAPI、python-multipart、requests、pytest、pytest-asyncio 升级；`pip check` 通过；`pip-audit` 仅剩 transformers 受 sentence-transformers 约束的 3 个 advisory。
- 性能：PostgreSQL sync adapter 增加小连接池；`/api/agents` 改轻量摘要、批量蓝图查询、短 TTL cache，不再列表同步探测 8001。
- 性能：Agent Run submit 缩短请求线程路径，成功审计转 background task，响应包含 `queue_job_id`；Redis 登录限流改 pipeline。
- 队列：RQ queue 拆为 `general/video/dataset/knowledge/blueprint`；生产 compose 已验证 `worker-general=4`、`worker-video=2` 运行。
- 验证：compileall 通过；unittest 35 tests OK；pytest 35 passed；ruff 通过；web build 通过；生产 compose rebuild/up/health 通过。
- 容量：20 用户 2m 0% 错误，aggregate p95 44ms；100 用户 2m 0% 错误，aggregate p95 140ms；100 用户 10m 0% 错误，aggregate p95 140ms，submit p95 520ms。
- 分布式：多 API SSE 做了 smoke，API A 创建 run，API B 收到 11 个 SSE 事件，事件未泄露 prompt/raw_response/workflow_options/token。
- 未完成：mypy 未通过；bandit 仍有中/低项；Redis pause/recovery、worker crash/recovery、50 视频队列、Dataset/Document/Blueprint 队列验收、完整 S3 权限、完整 pgvector 迁移、200/300/500 用户压测未执行。

### v1.8

- 新增 PostgreSQL/Alembic schema、22 张 APP 表、SQLite -> PostgreSQL 迁移脚本。
- 新增 Redis cache/rate-limit/distributed event bus、inline/RQ queue facade、worker entry、Agent Run Redis Pub/Sub wakeup。
- 新增 artifact storage facade、RAG provider facade、request id、metrics、`/health/live`、`/health/ready`、runtime health v1.8 component status。
- `agent_runs.row_version` 和终态保护落地；登录限流按 IP + username。
- Docker production 拓扑包含 PostgreSQL、Redis、MinIO、API、Web、Nginx、worker-general、worker-video。
- Alembic upgrade/re-run、SQLite -> PostgreSQL dry-run/execute/verify、MinIO 小样本、pgvector 小样本均已真实执行过。

### v1.7.2

- 蓝图发布 E2E、release gate、rollback、Registry/Blueprint sync、legacy JSON fallback 默认 false、SSE Event Hub、async store wrapper、Docker production build 配置。
- 后端 compileall/unittest/pytest、migration verify、web build、smoke、docker compose config 均曾通过。

### v1.7.1 / v1.7

- Blueprint center、版本、验证、测试、发布、回滚、导入导出。
- 视频拆解 seeded 为 published blueprint `bp_video_script_breakdown`。

### v1.6.x

- 视频拆解智能体生产化，真实调用本地 8001；不可达时真实 failed；artifact、Debug Payload、summary/result、SSE/polling 闭环。

### v1.5.x

- APP SQLite 迁移、APP/RAG SQLite 分离、Dataset、字段映射、清洗、导出、安全下载、QA/RAG、知识库、DeepSeek 流式问答。

### v1.2-v1.4

- 登录鉴权、角色权限、用户隔离、Connector、Payload Preview、Debug Replay、管理员、审计、权限。

## 当前正在处理的问题

最近用户要求只生成交接包，不继续写新功能。下一窗口恢复开发时，最优先仍是 `/agent` 回归：

1. `/agent` 智能体界面执行任务后，左侧聊天记录必须新增并持久保存。
2. 切换到其他路由再回来，任务和聊天不能消失。
3. 脚本/视频拆解智能体提交后必须真实调用后端和 local agent，不允许只创建 UI 状态。
4. 任务状态、结果、错误必须回写到对应聊天记录。

## 最近一次用户明确要求

为当前项目生成一个新窗口可继续接手的上下文交接包。不要继续写新功能，只做总结和落盘，更新 `docs/CODEX_HANDOFF.md`、`docs/NEXT_TASKS.md`、`docs/CHANGELOG_CONTEXT.md`、`AGENTS.md`。

## 已经改过的关键文件

- 安全/配置：`apps/api/services/security_config_service.py`、`apps/api/services/token_service.py`、`apps/api/services/user_store.py`、`.env.example`
- DB/生产路径：`apps/api/services/app_sqlite.py`、`apps/api/db/`、`alembic.ini`、`docker-compose.prod.yml`
- 队列/worker：`apps/api/tasks/`、`apps/api/workers/`、`apps/api/services/runtime_health_service.py`
- Agent run：`apps/api/routers/agent_runs.py`、`apps/api/services/task_store.py`、`apps/api/services/orchestrator.py`
- Conversation：`apps/api/services/conversation_store.py`、`apps/api/services/service_events.py`
- Redis/events/cache：`apps/api/services/redis_service.py`、`cache_service.py`、`rate_limit_service.py`、`agent_run_event_bus.py`
- Artifact/RAG：`apps/api/storage/`、`apps/api/rag/`、`apps/api/services/artifact_service.py`、`qa_rag_store.py`
- Frontend：`apps/web/src/app/agent/page.tsx`、`apps/web/src/components/*Agent*`、`DatasetPanel.tsx`、`KnowledgeBasePanel.tsx`、`RuntimeHealthPanel.tsx`
- Tests：`apps/api/tests/test_security_hardening.py`、`test_auth_service.py`、`test_agent_runs_api.py`、`test_agent_run_events_sse.py`
- Docs：`docs/CAPACITY_REPORT_V18.md`、`docs/SECURITY_HARDENING_V181.md`、`docs/PERFORMANCE_OPTIMIZATION_V181.md`、`docs/DISTRIBUTED_ACCEPTANCE_V181.md`

## 数据库/API/前端状态

- 当前生产 compose 已重建并保持运行：PostgreSQL healthy、Redis healthy、MinIO healthy、API healthy、Web healthy、Nginx running、worker-general x4、worker-video x2。
- `/health` 和 `/health/live` 返回 ok。
- `/health/ready` 返回 Postgres/Redis/queue/events/S3/pgvector/security ok。
- 登录后 `/api/admin/runtime/health` 返回 `version=v1.8.1`、`model=meizhaiseek 2.0`、database postgres、queue redis、events redis、artifact_storage s3、rag pgvector。
- 前端生产 build 通过。
- `ARCHITECTURE_EVALUATION_REPORT.md` 是用户既有未提交改动，已知第 793 行 trailing whitespace，不要擅自修改或 stage。

## 已知 bug / 风险

- `mypy` 还不是可用门禁：当前 top-level `services` / `tasks` 导入布局缺少 mypy path/config，且有真实类型问题。
- `bandit` 高危已归零，但仍有中/低项，主要是动态 SQL 片段和已防护 subprocess 的审计提示。
- `pip-audit` 剩余 `transformers 4.57.6` advisory，受 `sentence-transformers<5` 约束。
- P2 未完整验收：Redis pause/recovery、worker crash/recovery、50 视频队列、Dataset/Document/Blueprint 队列、完整 S3 权限、完整 pgvector 迁移都未执行。
- P3 200/300/500 用户压测未执行，不能写支持 500 用户已通过。
- `.env` 内有本机真实 secret/admin/loadtest 密码，不提交、不输出。
- runtime/logs/backups/uploads/models/node_modules 不提交。

## 不能破坏的功能

- v1.2 登录鉴权、角色权限、用户隔离。
- v1.3 Connector、Payload Preview、Debug Replay。
- v1.4 管理员、审计、权限。
- v1.5 Dataset、字段映射、清洗、导出、安全下载。
- v1.5.2-v1.5.6 QA/RAG、知识库、诊断、流式问答。
- v1.5.7 APP SQLite 迁移和 APP/RAG SQLite 分离。
- v1.5.8 conversation 增量 upsert、Dataset SQLite、service_events。
- v1.6+ 视频拆解真实执行、result normalizer、artifact、Debug Payload。
- v1.7+ Blueprint 描述层、视频拆解 published 蓝图、发布/回滚/测试/导入导出。
- v1.8+ PostgreSQL/Redis/RQ/S3/pgvector 生产路径和 SQLite 本地兼容。
- `/agent` 会话持久化、路由恢复、取消、重试、下载。
- `/chat` 流式问答。

## 下一窗口必须优先读取的文件

1. `AGENTS.md`
2. `docs/CODEX_HANDOFF.md`
3. `docs/NEXT_TASKS.md`
4. `docs/CHANGELOG_CONTEXT.md`
5. `docs/CAPACITY_REPORT_V18.md`
6. `docs/SECURITY_HARDENING_V181.md`
7. `docs/PERFORMANCE_OPTIMIZATION_V181.md`
8. `docs/DISTRIBUTED_ACCEPTANCE_V181.md`
9. `docs/API.md`
10. `docs/PRD.md`
11. `docs/TESTING.md`
12. `apps/web/src/app/agent/page.tsx`
13. `apps/web/src/hooks/useAgentRunEvents.ts`
14. `apps/api/routers/agent_runs.py`
15. `apps/api/services/conversation_store.py`
16. `apps/api/services/task_store.py`
17. `apps/api/tasks/queue.py`
18. `apps/api/workers/worker.py`

## 新窗口启动提示词

请继续接手 `E:\USE\codexhome\agents-cowork\meizhaiseek-platform`。当前版本是 `meizhaiseek v1.8.1`，模型名 `meizhaiseek 2.0`，当前分支 `main`，最近已推送提交仍是 `cae7884 refactor: stabilize architecture P1-P3 for v1.7.2`。请先完整读取 `AGENTS.md`、`docs/CODEX_HANDOFF.md`、`docs/NEXT_TASKS.md`、`docs/CHANGELOG_CONTEXT.md`、`docs/CAPACITY_REPORT_V18.md`、`docs/SECURITY_HARDENING_V181.md`、`docs/PERFORMANCE_OPTIMIZATION_V181.md`、`docs/DISTRIBUTED_ACCEPTANCE_V181.md`，再读取代码和 `git status --short`。当前工作区未提交，包含 v1.8/v1.8.1 改动和用户既有 `ARCHITECTURE_EVALUATION_REPORT.md` 改动；不要裸 `git add .`，不要提交 `.env`、runtime、logs、uploads、models、node_modules，也不要修改/暂存评估报告第 793 行 trailing whitespace。最优先任务是回归 `/agent`：任务提交后左侧聊天记录必须新增并持久保存；切路由回来任务/聊天不能消失；脚本/视频拆解智能体必须真实调用后端和 local agent；任务状态、结果、错误必须回写到对应聊天记录。不要破坏已有鉴权、Connector、Debug、管理员、Dataset、QA/RAG、SQLite、视频拆解、SSE/polling、Blueprint、Postgres/Redis/RQ/S3/pgvector 能力。
