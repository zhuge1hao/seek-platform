# Next Tasks

## v1.8.6 Current Priority

- Branch: `stabilization/v1.8.6`
- Version: `meizhaiseek v1.8.6`
- Model: `meizhaiseek 2.0`
- Protected dirty file: `ARCHITECTURE_EVALUATION_REPORT.md`

v1.8.4 backend video Agent E2E, worker crash/restart, zombie recovery, 50 video jobs, and Redis pause/recovery passed with real evidence. v1.8.6 now focuses on Dataset/Knowledge/Blueprint business queues, MinIO artifact storage, pgvector non-empty migration/resume, browser `/agent` smoke, and runtime marker closeout. Do not start v1.9, add new business agents, refactor local video Agent, change local video Agent Prompt, or run 200/300/500-user capacity tests in v1.8.6.

Acceptance marker defaults:

- `multi_instance_sse_verified=not_run`
- `redis_recovery_verified=passed` when the deployment environment sets `REDIS_RECOVERY_VERIFIED=passed`
- `worker_recovery_verified=passed` when the deployment environment sets `WORKER_RECOVERY_VERIFIED=passed`
- `video_queue_50_verified=passed` when the deployment environment sets `VIDEO_QUEUE_50_VERIFIED=passed`
- `dataset_queue_verified=not_run`
- `knowledge_queue_verified=not_run`
- `blueprint_queue_verified=not_run`
- `artifact_s3_verified=not_run`
- `pgvector_migration_verified=not_run`
- `browser_agent_smoke_verified=not_run`
- `capacity_last_verified_users=0`
- `capacity_last_test_passed=not_run`

v1.8.6 execution status on 2026-07-17:

- Docker daemon recovered and production compose is running.
- Dataset queue acceptance: `passed`.
- Knowledge queue acceptance: `failed`.
- Blueprint queue acceptance: `passed`.
- MinIO full permission/TTL/streaming acceptance remains `not_run`; signed URL and download smoke passed.
- pgvector non-empty dry-run/execute/verify passed; resume/top-k remains `not_run`.
- Browser `/agent` smoke remains `not_run`.
- New rerun entry points: `acceptance_dataset_queue.py`, `acceptance_knowledge_queue.py`, `acceptance_blueprint_queue.py`, `acceptance_minio_storage.py`, `acceptance_pgvector_nonempty.py`.

Latest P0 evidence:

- Success run: `run_20260716094829_ecf1360b`.
- Conversation: `conv_20260716094829_e4b8023b`.
- Queue job: `agent-run-run_20260716094829_ecf1360b`.
- DB rows: `agent_runs=1`, `agent_conversations=1`, `agent_messages=2`, `artifacts=260`, `debug_payloads=1`.
- Artifact downloads: Excel `passed`, JSON `passed`, evidence image `passed`, folder manifest `passed`.
- Shot consistency: `final_shots=45`, `data_columns=45`, `embedded_images=45`.
- Failure-path run: `run_20260716093735_2b597cc0`, terminal `failed`, one assistant failed message, no duplicate assistant message observed.
- Not executed: browser Run-card visual smoke, cancel/retry/user-isolation browser flows.

Latest P1 evidence:

- Worker recovery runs:
  - general: `run_20260716181405_cd91a5c3`, job `acceptance-worker-general-run_20260716181405_cd91a5c3`, final `failed`, passed.
  - video: `run_20260716181410_d867a363`, job `acceptance-worker-video-run_20260716181410_d867a363`, final `failed`, passed.
  - knowledge: `run_20260716181414_1a49583d`, job `acceptance-worker-knowledge-run_20260716181414_1a49583d`, final `failed`, passed.
  - dataset: `run_20260716181418_21f5a012`, job `acceptance-worker-dataset-run_20260716181418_21f5a012`, final `failed`, passed.
  - blueprint: `run_20260716181423_15894ff1`, job `acceptance-worker-blueprint-run_20260716181423_15894ff1`, final `failed`, passed.
- Zombie stale run: `run_20260716181429_b42b4460`, final `failed`, passed.
- 50 video jobs: submitted `50`, mock `48`, real `2`, completed `49`, failed `0`, cancelled `1`, max executing `2`, final queued/started `0`.
- Redis recovery: run `run_20260716181758_d2867ca8`, post-recovery run `run_20260716181802_b723d0bd`, pause `1.064s`, recovery `0s`, event p95 `2.014s`, passed.
- Not executed: P2 Dataset/Knowledge/Blueprint business queue acceptance, P3 MinIO/backup validation, 100/200/300/500-user v1.8.4 capacity tests.

## Current State

- Branch: `stabilization/v1.8.3`
- HEAD: `d83603213ed34fc315d783a98aa1c51467f288f3`
- Version: `meizhaiseek v1.8.3`
- Model: `meizhaiseek 2.0`
- Protected dirty file: `ARCHITECTURE_EVALUATION_REPORT.md`

P0/P1 v1.8.3 infra and quality work is pushed. The next priority is `/agent` user-facing correctness. Do not start v1.9 or broad infra work until P0 below is proven.

## P0 - `/agent` Real Task And Chat Loop

### P0.1 Conversation Created And Persisted After Submit

Goal:

- After submitting a task in `/agent`, the left conversation list immediately includes the new or updated backend conversation.
- Backend persists matching conversation, user message, assistant run message, and run rows.

Files:

- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/components/AgentWorkspace.tsx`
- `apps/web/src/components/GenericAgentPanel.tsx`
- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/web/src/hooks/useAgentConversations.ts`
- `apps/api/routers/agent_runs.py`
- `apps/api/routers/conversations.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`

Acceptance:

- `POST /api/agent-runs` returns real `run_id`, `conversation_id`, and `queue_job_id` in Redis/RQ mode.
- `GET /api/conversations` includes the new conversation after submit.
- `agent_conversations`, `agent_messages`, and `agent_runs` contain matching rows.
- Refreshing the page keeps the conversation.
- User A cannot read User B conversations.
- Current dirty frontend change in `page.tsx` must be verified or adjusted, not blindly trusted.

### P0.2 Route Switch Restore

Goal:

- Switching from `/agent` to another route and back does not lose active task/chat/run state.

Files:

- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/hooks/useAgentRunEvents.ts`
- `apps/web/src/hooks/useAgentRunPolling.ts`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`

Acceptance:

- Restore priority is URL `conversation_id`, then stored active id, then latest backend conversation, then empty state.
- Running run reconnects to SSE first.
- Polling starts only after SSE failure.
- Completed/failed/cancelled runs stop polling/streaming.
- Invalid active id clears cleanly without blank screen.
- Fast conversation switching ends on the latest selected conversation.

### P0.3 Script/Video Breakdown Must Really Execute

Goal:

- Script/video breakdown submit executes through backend queue/workflow/local Agent, not just UI state.

Files:

- `apps/api/routers/agent_runs.py`
- `apps/api/tasks/queue.py`
- `apps/api/workflows/video_script_workflow.py`
- `apps/api/services/local_agent_client.py`
- `apps/api/services/video_agent_payload_builder.py`
- `apps/api/services/video_breakdown_result_normalizer.py`
- `apps/api/services/artifact_service.py`
- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `docker-compose.prod.yml`

Acceptance:

- Frontend only calls platform backend, never `8001` directly.
- Redis/RQ mode returns quickly and records `queue_job_id`.
- 8001 unavailable produces a real failed run with clear error.
- 8001 available calls `/run` and persists result/artifacts/debug payload.
- Debug payload request is the actual backend-to-8001 payload.
- `worker-video` receives video jobs in Docker production mode.

### P0.4 Status, Result, Error Write Back To Chat

Goal:

- Task lifecycle is visible in the matching chat record.

Files:

- `apps/api/services/service_events.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`
- `apps/api/services/agent_run_event_bus.py`
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/components/ConversationMessages.tsx`
- `apps/web/src/hooks/useAgentRunEvents.ts`

Acceptance:

- Running is visible in the assistant message.
- Completed writes result summary and artifact links.
- Failed writes sanitized error summary.
- Cancelled writes cancelled state.
- Multiple conversations/runs do not cross-update each other.

## P1 - Regression Tests And Smokes

Goal:

- Add/keep the smallest tests that prove the `/agent` loop is real and persistent.

Files:

- `apps/api/tests/test_agent_runs_api.py`
- `apps/api/tests/test_conversation_store.py`
- `apps/api/tests/test_agent_run_events_sse.py`
- Frontend/browser smoke only if an existing lightweight pattern is available.

Acceptance:

- `python -m unittest discover -s apps/api/tests` passes.
- `python -m pytest apps/api/tests` passes.
- `apps/web`: `npm.cmd run build` passes after frontend changes.
- Tests cover conversation/message/run persistence, user isolation, terminal status protection, and event payload redaction.
- Add one real API/browser smoke for submit -> conversation list -> route restore if practical.

## P1.5 - DeepSeek Production Env Follow-Up

Goal:

- Keep DeepSeek config available to API and workers without leaking secrets.

Files:

- `.env` (local secret file, never commit)
- `docker-compose.prod.yml`
- `apps/api/services/deepseek_client.py`
- `apps/api/routers/qa_chat.py`

Acceptance:

- `DEEPSEEK_API_KEY` is present in API and worker containers.
- `/health/ready` reports `ok` for security/QA-related readiness.
- QA model status reports DeepSeek configured.
- No key appears in git diff, logs, docs, or final output.

## P2 - Production Acceptance Still Pending

Goal:

- Continue only after P0/P1 are green.

Tasks:

- Redis pause/recovery SSE with two API instances.
- Worker crash/restart/zombie recovery with a controlled long task.
- 50 video jobs with video worker concurrency cap.
- Dataset/Knowledge/Blueprint real Docker queue consumption.
- MinIO permission/TTL/streaming chain.
- pgvector production corpus migration only if real data and rollback plan are ready.
- 200/300/500 user Locust only after P2 critical gates pass.

Acceptance:

- Each test is actually executed.
- Not executed stays documented as `not executed`.
- Failed stays documented as `not passed`.
- Do not claim 500-user support without the real 500-user run.

## Current Known Blocks

- `ARCHITECTURE_EVALUATION_REPORT.md` is protected dirty user work.
- Docker was not running during the 2026-07-16 handoff check; live health was not reverified in this handoff turn.
- Dataset export queue has no public enqueue endpoint.
- Standalone dataset/knowledge/blueprint workers are not configured; `worker-general` consumes those queues.
- Raw `pip-audit` still fails unless exact documented `transformers 4.57.6` exceptions are applied.
- Existing Redis/worker integration tests are marker tests, not true fault-injection automation.
