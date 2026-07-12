# Next Tasks

## v1.8.3 Current Plan - 2026-07-12

Completed baseline:

- Branch target: `stabilization/v1.8.3`.
- Base commit: `51913b4f8eb5e34e9fb170c4fe524c71ae28c6f4`.
- Protected dirty file remains `ARCHITECTURE_EVALUATION_REPORT.md`; do not stage it.

Next:

- P0: passed and ready to push.
- P1: queue closure, pgvector non-empty validation, dependency exception review.
- P2/P3: run only after earlier gates pass; unexecuted items must remain marked `not executed`.

## v1.8.2 Current State - 2026-07-10

Completed this round:

- P0 was committed and pushed as `645bea682a54d2ffe670a41631ffbf44f5ad6221`.
- Full `mypy apps/api` now passes.
- Redis client reuse, Redis error redaction, cache sensitive-entry refusal, QA enqueue tests, and Blueprint queue entry points are encoded.
- `worker-general` compose queue list is now `general,dataset,knowledge,blueprint`.
- BGE-small-zh SQLite and pgvector smoke passed.
- Non-empty pgvector migration smoke passed with 5 documents and 50 chunks.
- 100-user 15-minute Locust run passed minimum latency/error gate and queue depth recovered to 0 after scaling `worker-general=4`.
- P2 partial technical debt pass: one conversation B608 site removed, conversation incremental-write tests added, remaining simple SWR hooks moved to `useApiQuery`, and Agent Run SSE backoff encoded.

Still blocked / not executed:

- Raw `pip-audit` still fails for three documented `transformers 4.57.6` advisories.
- P2 worker crash/restart and zombie recovery are not executed in this round.
- P2 50 video jobs are not executed.
- P2 real Dataset/Knowledge/Blueprint Docker worker acceptance is not fully executed.
- JSON DB migration for `agent_config_store` and `skill_template_service` is not executed.
- P3 200/300/500 users remain not executed.

Next recommended step:

- Continue P2 with real worker crash/restart and queue acceptance after the P1 commit is pushed; do not start P3 until P2 critical gates pass.

## v1.8.2 Current State - 2026-07-07

Immediate state:

- Docker Desktop / Linux Engine recovered and production compose is running.
- Running services: PostgreSQL healthy, Redis healthy, MinIO healthy, API healthy, Web healthy, Nginx running, `worker-general` running, `worker-video` running.
- Not configured in compose: standalone `worker-dataset`, `worker-knowledge`, `worker-blueprint`.
- Alembic is at `20260705_v18_initial (head)`.
- APP SQLite -> PostgreSQL restore executed and verified.
- pgvector restore path executed with zero RAG source documents/chunks; full RAG data migration remains not executed.
- Schema parity script passed.
- Login smoke and SSE smoke passed.
- `/health/ready` is currently degraded because the admin password was restored to the legacy default at the user's request.

Next mandatory work:

- Replace the legacy default admin password with a strong production password before claiming readiness is fully green.
- Continue P2 only after recording the current degraded readiness honestly.
- Remaining P2: real Redis pause/recovery acceptance, worker crash/restart, zombie recovery, dataset queue, knowledge queue, blueprint queue, MinIO permissions/TTL/streaming, pgvector resume verification, 50 video jobs.
- P3 remains blocked until P2 critical gates pass.

## v1.8.2 Current Gate

Current version: meizhaiseek v1.8.2

P1 quality gates have passed the minimum acceptance threshold. Agent submit p95 remains 未通过 for the <=500ms priority target; the latest 100-user operator-pool run measured p95=600ms.

P2 is partially executed:

- Redis pause/recovery SSE: 已通过.
- Zombie maintenance recovery: 已通过.
- Full worker crash/restart/retry: 未执行.
- 50 video queue, Dataset queue, Document ingest queue, Blueprint queue, full MinIO, pgvector migration, schema parity: 未执行.

Do not start P3 until the remaining P2 gates pass.

当前版本：meizhaiseek v1.8.1

原则：先修真实链路，再做 UI 增强。后端数据库和任务队列是事实来源；前端不能伪造任务、会话、结果或错误。

## P0：/agent 真实任务链路回归

### P0.1 提交任务后左侧聊天记录必须新增并持久保存

目标：用户在 `/agent` 提交任务后，后端创建或更新 Agent Conversation；左侧列表立即出现真实会话；数据库中有 conversation/message/run。

涉及文件：

- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/hooks/useAgentRunEvents.ts`
- `apps/web/src/hooks/useAgentRunPolling.ts`
- `apps/api/routers/agent_runs.py`
- `apps/api/routers/conversations.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`
- `apps/api/services/service_events.py`

验收标准：

- `POST /api/agent-runs` 返回真实 `run_id`、`conversation_id`、`queue_job_id`。
- `GET /api/conversations` 立即包含新会话。
- `agent_conversations`、`agent_messages`、`agent_runs` 都有对应记录。
- 刷新页面后左侧记录仍存在。
- 用户 A 不能读取用户 B 的会话。

### P0.2 切换到其他路由再回来，任务/聊天不能消失

目标：从 `/agent` 切到 `/chat`、后台或其他路由后再回来，恢复 active conversation、messages、latest run、status、result/error。

涉及文件：

- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/hooks/useAgentRunEvents.ts`
- `apps/web/src/hooks/useAgentRunPolling.ts`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`

验收标准：

- 恢复优先级：URL `conversation_id` -> localStorage active id -> 后端最近会话 -> 空状态。
- running run 恢复后继续 SSE；SSE 失败才启用 polling。
- completed/failed/cancelled 不重复轮询。
- 无效 active id 被清理，不白屏。
- 快速切换会话后最终显示最后一次选择。

### P0.3 脚本/视频拆解智能体提交后必须真实执行

目标：`/agent` 只调用平台后端 `POST /api/agent-runs`；后端对 `agent_type=video_script_breakdown` 进入队列和 workflow；8001 不可达时真实 failed，8001 可达时真实 POST `/run`。

涉及文件：

- `apps/api/routers/agent_runs.py`
- `apps/api/tasks/queue.py`
- `apps/api/workflows/video_script_workflow.py`
- `apps/api/services/video_agent_payload_builder.py`
- `apps/api/services/local_agent_client.py`
- `apps/api/services/video_breakdown_result_normalizer.py`
- `apps/api/services/artifact_service.py`
- `apps/api/scripts/smoke_minimal.py`
- `apps/web/src/app/agent/page.tsx`

验收标准：

- Debug Payload request 是真实发给 8001 的 `/run` payload。
- Redis/RQ 模式下 API 立即返回，不等待视频处理完成。
- 8001 不可达时 run.status 为 `failed`，错误清晰。
- 8001 可达时 run 真实 running/completed，result_json 和 artifacts 持久化。
- 不允许前端直接连 8001。

### P0.4 任务状态、结果、错误回显到对应聊天记录

目标：`running/completed/failed/cancelled` 通过 `service_events` / event bus 同步到对应 conversation assistant message；completed 显示 summary/artifacts；failed 显示错误；retry 保留旧 run 并创建新 run。

涉及文件：

- `apps/api/services/service_events.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`
- `apps/api/services/agent_run_event_bus.py`
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/hooks/useAgentRunEvents.ts`

验收标准：

- running 状态能在聊天记录中看到。
- completed 后对应 assistant message 显示结果摘要和下载。
- failed 后对应 assistant message 显示错误摘要。
- cancelled 显示任务已取消。
- 多会话、多 run 并存时状态不串线。

## P1：v1.8.1 质量门禁补齐

### P1.1 Bandit 中风险收敛

目标：把剩余 Bandit Medium/Low 逐项分类：真实修复或精确标记误报。不要全局关闭 Bandit。

涉及文件：

- `apps/api/db/repositories/postgres.py`
- `apps/api/rag/pgvector_provider.py`
- `apps/api/routers/agents.py`
- `apps/api/scripts/migrate_sqlite_to_postgres.py`
- `apps/api/services/*_store.py`
- `apps/api/services/local_agent_client.py`

验收标准：

- `python -m bandit -r apps/api -x apps/api/tests,apps/api/runtime,apps/api/models` 无 High。
- 每个保留的 `# nosec` 都有具体原因。
- 不弱化 table allowlist、CLI command guard、auth、user isolation。

### P1.2 pip-audit 剩余 transformers 风险决策

目标：处理 `transformers 4.57.6` 剩余 advisory；如果 `sentence-transformers` 仍约束 `<5`，记录风险和替代方案，不假装通过。

涉及文件：

- `apps/api/requirements.txt`
- `docs/SECURITY_HARDENING_V181.md`
- `docs/CAPACITY_REPORT_V18.md`

验收标准：

- `python -m pip_audit` 真实执行。
- 若仍未通过，文档写明包名、版本、限制、后续升级路径。

### P1.3 mypy 最小可用门禁

目标：不要做全仓库类型大重写。先让高风险新增模块可被 mypy 检查。

涉及文件：

- `pyproject.toml`
- `apps/api/services/security_config_service.py`
- `apps/api/services/app_sqlite.py`
- `apps/api/services/local_agent_client.py`
- `apps/api/tasks/`
- `apps/api/workers/`

验收标准：

- mypy 使用明确 path 配置，不依赖隐式当前目录。
- 新增/高风险模块 scoped mypy 通过，或文档明确剩余类型问题。

## P2：分布式链路验收

### P2.1 Redis Pub/Sub SSE 完整验收

目标：完成 smoke 之外的多实例 SSE 验收，包括 Redis 暂停/恢复和资源释放。

涉及文件：

- `apps/api/services/agent_run_event_bus.py`
- `apps/api/routers/agent_runs.py`
- `apps/web/src/hooks/useAgentRunEvents.ts`
- `docs/DISTRIBUTED_ACCEPTANCE_V181.md`

验收标准：

- API A 创建 run，API B SSE 收到 status/progress/completed/failed。
- Redis 暂停时 fallback polling 生效。
- Redis 恢复后重新订阅。
- 用户 A 不能订阅用户 B run。
- 事件不包含 prompt、raw_response、workflow_options、token。
- 真实通过后才允许 runtime health 设置 `events.multi_instance_verified=true`。

### P2.2 Worker crash/restart/zombie recovery

目标：真实杀 worker 后，任务不永久 running；重启后重试、interrupted 或 failed 策略明确。

涉及文件：

- `apps/api/workers/worker.py`
- `apps/api/services/agent_run_maintenance.py`
- `apps/api/services/task_store.py`
- `apps/api/tasks/`
- `docs/DISTRIBUTED_ACCEPTANCE_V181.md`

验收标准：

- 提交长时间 mock job。
- worker 开始执行后终止进程。
- zombie maintenance 生效。
- 不重复生成 artifact。
- cancelled 任务不恢复执行。
- 达最大重试后停止。

### P2.3 50 视频任务队列并发验收

目标：用 mock 视频任务验证 video worker 并发上限，避免视频任务阻塞 general queue。

涉及文件：

- `apps/api/tasks/queue.py`
- `apps/api/tasks/video_tasks.py`
- `apps/api/workers/worker.py`
- `docker-compose.prod.yml`
- `load_tests/`

验收标准：

- 快速提交 50 个视频任务。
- `worker-video=2` 时同时 executing 不超过 2。
- 其余任务 queued。
- general queue 不阻塞登录、读取、Agent 列表。
- 最终 queued=0、executing=0。

### P2.4 Dataset/Document/Blueprint 队列验收

目标：验证 dataset clean/export、document ingest、blueprint test run 在 Redis/RQ 模式下真实入队、执行、持久化。

涉及文件：

- `apps/api/routers/datasets.py`
- `apps/api/routers/qa_knowledge.py`
- `apps/api/routers/agent_blueprints.py`
- `apps/api/tasks/dataset_tasks.py`
- `apps/api/tasks/knowledge_tasks.py`
- `apps/api/tasks/blueprint_tasks.py`

验收标准：

- API 快速返回 `job_id`。
- worker 写 running/progress/result/error。
- 幂等、取消、失败、重试、用户隔离可验证。
- 结果和 artifact 持久化。

### P2.5 S3/MinIO 和 pgvector 完整链路

目标：完成小样本之外的权限、流式、迁移验收。

涉及文件：

- `apps/api/storage/`
- `apps/api/routers/artifacts.py`
- `apps/api/rag/`
- `apps/api/scripts/`
- `docs/ARTIFACT_STORAGE.md`
- `docs/RAG_BACKENDS.md`

验收标准：

- 用户 A 上传/下载，用户 B 不能下载。
- object_key 不允许目录穿越。
- API 不返回 S3 credentials。
- 大文件下载不一次性读入内存。
- pgvector migration 支持 dry-run/execute/verify/resume/checkpoint。

## P2：/agent 回归自动化

### P2.6 后端回归测试补齐

目标：用最少测试覆盖 P0，不污染 runtime。

涉及文件：

- `apps/api/tests/test_agent_runs_api.py`
- `apps/api/tests/test_conversation_store.py`
- `apps/api/tests/test_agent_run_events_sse.py`

验收标准：

- `python -m unittest discover -s apps/api/tests` 通过。
- `python -m pytest apps/api/tests` 通过。
- 测试验证 conversation/message/run 同步、用户隔离、terminal status 防覆盖。

## P2：文档和交付

### P2.7 提交前保护

目标：只 stage 确认范围，保护用户既有改动和运行产物。

涉及文件：

- `AGENTS.md`
- `.gitignore`
- `ARCHITECTURE_EVALUATION_REPORT.md`

验收标准：

- `git status --short` 已审查。
- `git diff --check` 只允许已知用户文件问题，不能新增 whitespace。
- 不 stage `.env`、`.venv`、runtime、logs、backups、uploads、models、node_modules、Locust raw large files、secrets。
- 不 stage `ARCHITECTURE_EVALUATION_REPORT.md`，除非用户明确要求。

## P3：容量扩展

### P3.1 200/300/500 用户阶段压测

目标：只有 P1/P2 门禁通过后才执行。100 用户必须先稳定。

涉及文件：

- `load_tests/locustfile.py`
- `docs/CAPACITY_REPORT_V18.md`
- `docs/SCALABILITY_500_USERS.md`

验收标准：

- 200 用户 5 分钟、300 用户 10 分钟、500 用户 15 分钟按阶段执行。
- 错误率、p50/p95/p99、CPU/RAM、DB pool、Redis latency、queue depth、SSE 连接都记录。
- 未达标就写未通过；资源不足就写未执行/未完成，不写支持 500 已通过。
