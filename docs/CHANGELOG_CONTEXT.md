# Changelog Context

## v1.8.3 Start - 2026-07-12

- Created from `stabilization/v1.8.2` at `51913b4f8eb5e34e9fb170c4fe524c71ae28c6f4`.
- Scope: full type gate revalidation, queue closure, pgvector non-empty validation, and production acceptance hardening.
- Out of scope: new business agents, v1.9 upgrade, local video Agent prompt changes, and unverified 500-user claims.

## v1.8.2 Docker Recovery Update - 2026-07-07

- Restored Docker Desktop Linux Engine on `desktop-linux` without destructive WSL/Docker operations.
- Verified relocated Docker data disk symlink from the Docker Desktop default VHDX path to `E:\USE\Docker\docker-desktop-disk\docker_data.vhdx`.
- Rebuilt production Docker topology from empty Docker resources.
- Started and verified PostgreSQL, Redis, MinIO, API, Web, Nginx, `worker-general`, and `worker-video`.
- Ran Alembic to `20260705_v18_initial (head)`.
- Restored APP data from host SQLite into PostgreSQL and verified table counts.
- Enabled pgvector and ran RAG migration dry-run/execute/verify with zero source documents/chunks.
- Verified `/health`, `/health/live`, `/health/ready` before password rollback, `/metrics`, login, runtime health, Agent Run enqueue, and SSE smoke.
- At the user's request, restored the local admin password to the legacy default. After that rollback, `/health/ready` is degraded by design because `default_admin_password_detected=true`.
- No source code was changed during service recovery. Runtime backups, `.env`, uploads, logs, and Docker data remain uncommitted.
- P2 remains incomplete. Do not claim 500-user capacity or full distributed acceptance.

## v1.8.2 Current Status - 2026-07-06

- Current code/runtime version: `meizhaiseek v1.8.2`.
- Model display name remains `meizhaiseek 2.0`.
- P1 minimum quality/capacity gates: passed.
- P1 priority target not met: Agent submit p95 was 600ms in the final 100-user 10m operator-pool run, so submit p95 <=500ms is 未通过.
- Backend tests: `unittest` 53 OK; `pytest` 53 passed, 2 skipped, 2 warnings.
- Quality: compileall, ruff, scoped mypy, web build, docker compose config/build passed.
- Bandit: High=0, Medium=0, Low=33. High/Medium gate script passed.
- pip-audit: raw scan 未通过 for three `transformers 4.57.6` advisories; exact temporary exceptions are documented in `docs/SECURITY_EXCEPTIONS.md`.
- P2 Redis pause/recovery SSE: passed with two API instances; runtime health has `multi_instance_sse_verified=passed`.
- P2 zombie maintenance: controlled stale running repair passed; full worker crash/restart/retry remains 未执行, so `worker_recovery_verified=not_run`.
- P2 remaining gates are 未执行: 50 video queue, Dataset queue, Document ingest queue, Blueprint queue, full MinIO, pgvector migration, schema parity.
- P3 100/200/300/500 user capacity validation: 未执行 because P2 is incomplete.
- No commit or push has been performed for v1.8.2 in this partial pass.

## 当前状态

- 当前版本：meizhaiseek v1.8.1
- 模型名：meizhaiseek 2.0
- 当前分支：main
- 最近已推送提交：`cae7884 refactor: stabilize architecture P1-P3 for v1.7.2`
- GitHub：`https://github.com/zhuge1hao/seek-platform.git`
- 本地路径：`E:\USE\codexhome\agents-cowork\meizhaiseek-platform`
- 当前工作区：未提交，包含 v1.8/v1.8.1 改动和用户既有 `ARCHITECTURE_EVALUATION_REPORT.md` 改动。

## v1.8.1：安全加固、100 用户性能收敛与分布式链路验收

完成内容：

- 安全配置：生产模式不再使用公开固定 JWT 默认密钥；本地开发自动生成 runtime secret；runtime health 不泄露 secret。
- 管理员初始密码：生产禁止 `admin123`；支持强 `INITIAL_ADMIN_PASSWORD`；已存在管理员不覆盖密码；readiness 暴露 `default_admin_password_detected`。
- SQL/CLI：`table_count()` 增加表名白名单；local CLI connector 改 `shell=False`，拒绝 shell metacharacters。
- 异常/哈希：cache/conversation/payload preview 等静默异常改脱敏日志；dataset 和 legacy migration ID 从 SHA1 改 SHA256。
- 依赖：FastAPI 0.139.0、python-multipart 0.0.32、requests 2.34.2、pytest 9.1.1、pytest-asyncio 1.4.0。
- 性能：PostgreSQL sync adapter 增加小连接池；`/api/agents` 轻量摘要 + 批量蓝图查询 + TTL cache；Agent Run submit 缩短请求线程；Redis 登录限流 pipeline。
- 队列：RQ queue 拆分为 `general/video/dataset/knowledge/blueprint`；生产 compose 验证 `worker-general=4`、`worker-video=2`。
- 文档：新增 `SECURITY_HARDENING_V181.md`、`PERFORMANCE_OPTIMIZATION_V181.md`、`DISTRIBUTED_ACCEPTANCE_V181.md`，更新容量报告。

验证记录：

- `python -m compileall apps/api` 通过。
- `python -m unittest discover -s apps/api/tests` 通过，35 tests。
- `python -m pytest apps/api/tests` 通过，35 passed。
- `ruff check apps/api` 通过。
- `apps/web npm.cmd run build` 通过。
- Docker production rebuild/up 通过，PostgreSQL/Redis/MinIO/API/Web/Nginx/worker-general x4/worker-video x2 均运行。
- `/health`、`/health/live`、`/health/ready`、`/metrics` 通过。
- 登录后 `/api/admin/runtime/health` 返回 `version=v1.8.1`、`model=meizhaiseek 2.0`、Postgres/Redis/queue/S3/pgvector ok。
- Locust 20 用户 2 分钟：0% 错误，aggregate p95 44ms。
- Locust 100 用户 2 分钟：0% 错误，aggregate p95 140ms。
- Locust 100 用户 10 分钟：0% 错误，aggregate p95 140ms，p99 310ms，`/api/agents` p95 87ms，login p95 330ms，submit p95 520ms。

未完成/未通过：

- `bandit` 未全绿，但 High 为 0；剩余 Medium/Low 需要逐项修复或精确说明。
- `pip-audit` 未全绿；剩余 `transformers 4.57.6` advisories 受 `sentence-transformers<5` 约束。
- `mypy` 未通过；需要 path/config 和少量类型修复。
- Redis pause/recovery SSE fallback 未执行。
- Worker crash/restart/zombie recovery 未执行。
- 50 视频任务队列并发未执行。
- Dataset/Document/Blueprint 队列验收未执行。
- 完整 S3 权限/TTL/大文件流式链路未执行。
- 完整 SQLite RAG -> pgvector resumable migration 未执行。
- 200/300/500 用户压测未执行。

## v1.8：500 用户并发扩展与分布式生产架构

完成内容：

- 新增 `APP_DB_BACKEND=sqlite|postgres`、SQLAlchemy async、asyncpg、Alembic 和 22 张 APP 表 PostgreSQL schema。
- 新增 `migrate_sqlite_to_postgres.py`，支持 dry-run、execute、verify、table、batch-size、json-report。
- 新增 Redis/cache/rate limit/distributed event bus 服务。
- 新增 inline/RQ queue facade、worker entry 和 Agent Run enqueue。
- 新增 Agent Run Redis Pub/Sub wakeup，SSE 协议保持不变。
- 新增 `agent_runs.row_version` 和终态保护。
- 登录限流按 IP + username，429 + `Retry-After`。
- Artifact metadata 增加 storage backend/object key/checksum，新增 local/local_shared/S3 facade。
- 新增 RAG provider facade，SQLite 默认，pgvector 生产预留/小样本验证。
- 新增 `/health/live`、`/health/ready`、`/metrics`、request id、runtime health v1.8 组件状态。
- 更新 Docker production 拓扑：postgres、redis、minio、api、worker-general、worker-video、web、nginx。
- 新增 Locust 脚本和 v1.8 生产/容量/迁移/观测文档。

验证记录：

- Alembic `upgrade head` 和重复执行通过，head 为 `20260705_v18_initial`。
- SQLite -> PostgreSQL dry-run/execute/verify 主机环境通过。
- MinIO 小样本上传/下载/checksum/content-type 通过。
- pgvector 小样本 ingest/search/delete/user 隔离通过。
- 后端 compileall/unittest/pytest、前端 build、docker compose config 通过。

## v1.7.2：架构评估 P1-P3 稳定化

- 后端/前端/runtime health 版本更新到 `v1.7.2`。
- 新增蓝图完整发布 E2E 测试，覆盖 draft、validate、test_run、release gate、publish、rollback、disabled/deprecated 阻止新任务。
- 拆分 `agent_blueprint_store.py` 为 core/version/test/release store，原文件保留 facade。
- legacy JSON fallback 默认 false，新增 usage 统计和迁移完整性脚本。
- Web Dockerfile 改三阶段生产构建，prod compose 使用 build + start、healthcheck、restart、runtime/uploads volume。
- Agent Run SSE 新增 Event Hub；SQLite heartbeat 和 polling fallback 保留。
- Blueprint methodology 支持原生 HTML5 drag-and-drop 排序。
- 前端 API 兼容拆分，旧 `api.ts` re-export，新实现位于 `apps/web/src/lib/api/index.ts`。
- 新增 Registry/Blueprint 对账 preview/apply，只创建 draft，不自动发布。

验证记录：

- compileall、unittest、pytest、migration verify、web build、smoke、docker compose config 曾通过。

## v1.7.1 / v1.7：Blueprint 治理

- 完成 release gate、publish、rollback、diff、validation history、test runs、seed。
- 新增 Blueprint SQLite 表、store、service、validator、import/export、API、后台页面。
- 视频拆解 seeded 为 `bp_video_script_breakdown` published 蓝图。

## v1.6.x：视频拆解生产化与实时状态

- 视频拆解智能体真实调用本地 8001，不伪造 completed。
- 8001 不可达时任务真实 failed。
- 标准化 result_json、artifact、Debug Payload。
- Agent Run SSE events 和 polling fallback。
- summary/result 分离，避免大字段拖慢 UI。

## v1.5.x：SQLite、Dataset、QA/RAG

- APP SQLite 迁移，APP/RAG SQLite 分离。
- Dataset metadata 迁入 APP SQLite。
- Dataset 字段映射、清洗、导出、安全下载。
- QA/RAG、知识库、DeepSeek 流式问答、模型诊断。

## v1.2-v1.4：基础治理

- 登录鉴权、角色权限、用户隔离。
- Connector、Payload Preview、Debug Replay。
- 管理员、审计、权限、安全 UI。

## 下一窗口注意

- 第一优先级仍是 `/agent` 真实任务链路回归。
- P1 最低 100 用户门禁已通过，但 P2 分布式验收未完整通过，所以不要执行或宣称 500 用户通过。
- `.env` 有本机 secret/admin/loadtest 密码，不能提交或输出。
- `ARCHITECTURE_EVALUATION_REPORT.md` 是用户既有未提交改动，已知第 793 行 trailing whitespace，不要擅自修改或 stage。
- 不要提交 runtime、logs、backups、uploads、models、node_modules、`.next`。
