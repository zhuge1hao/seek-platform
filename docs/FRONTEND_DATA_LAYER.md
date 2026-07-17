# Frontend Data Layer

v1.6.5 保留 `apps/web/src/lib/api.ts` 作为唯一 HTTP、鉴权和错误处理层。SWR hooks 只调用 `api.ts` 中的函数，不绕过 token、401、403 和后端不可达处理。

## 已接入 SWR 的读取场景

- Runtime health、storage health、current user。
- Agent conversations、QA conversations。
- Knowledge stats、model status、knowledge documents。
- Agent connectors、agent configs、skill templates。
- Debug Payload list。
- Dataset list、uploaded files、mapping templates。
- Admin users。

## 不适合 SWR 的接口

- POST、PUT、DELETE。
- 上传、下载、blob preview。
- 任务提交、取消、重试、replay。
- `/agent` run summary/result 状态更新。
- 超大 Debug Payload 详情。

## mutate 规则

写操作成功后，只刷新相关 key：

- 新建或归档会话后 mutate conversations。
- 更新 Connector 后 mutate connectors。
- 更新用户后 mutate admin users。
- Dataset 清洗或删除后 mutate datasets 和 files。

## /agent 状态边界

运行中的 run 优先使用 `useAgentRunEvents`。SSE 失败后才启用 `useAgentRunPolling`。SWR 不参与 run 状态高频刷新。

## meizhaiseek v1.7.2

v1.7.2 focuses on architecture stabilization after the 2026-07-03 evaluation: Blueprint release E2E coverage, wider auth/conversation/task tests, Blueprint Store splitting, legacy JSON fallback retirement diagnostics, production Docker build/start, Agent Run SSE tests, async SQLite read wrappers, frontend API module compatibility split, methodology drag ordering, Registry/Blueprint reconciliation, and the Agent Run Event Hub. Existing Agent, Workflow, Connector, APP SQLite, RAG SQLite, Dataset, QA/RAG, Debug Payload, and video breakdown execution models are unchanged.

## meizhaiseek v1.8.2

已编码:

- `apps/web/src/lib/api/index.ts` is a pure barrel export.
- `apps/web/src/lib/api/core.ts` is the only place defining `API_BASE_URL`, `apiFetch`, token header injection, 401 cleanup, JSON error parsing, and blob download helpers.
- `apps/web/src/lib/api/stream.ts` owns fetch-streaming helpers for agent run SSE and QA streaming. Bearer tokens stay in headers and are not placed in URLs.
- Domain implementations are split across `auth`, `agents`, `agentRuns`, `blueprints`, `connectors`, `conversations`, `datasets`, `files`, `knowledge`, `qa`, and `admin`.
- `apps/web/src/lib/authStorage.ts` isolates token/user localStorage helpers and avoids an auth/core import cycle.
- `apps/web/src/hooks/useApiQuery.ts` wraps common SWR defaults while leaving business hooks responsible for keys and return types.
- Root, agent result, chat stream, Blueprint, Dataset, and Knowledge high-risk render surfaces are protected by error boundaries.

已验证:

- `npm.cmd run build` passed with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`.

未执行:

- Browser-level visual regression for every protected boundary.
- Runtime SSE reconnect/fallback P2 fault tests.

## meizhaiseek v1.8.2 P2 frontend update, 2026-07-10

已编码:

- Remaining simple direct SWR hooks now call `useApiQuery`: agent configs, agent connectors, admin users, current user, files, runtime health, storage health, skill templates, and debug payloads.
- Agent Run SSE reconnect now uses exponential backoff of 1s, 2s, 4s, 8s, 16s, then max 30s with jitter.
- Browser `online` triggers an immediate SSE retry.
- 401, 403, and 404 SSE failures do not retry forever.
- Terminal run statuses still stop SSE; route unmount and run switch still abort the active stream.
- Polling fallback remains active only after SSE failure and is stopped when SSE reconnects.

已执行:

- `npm.cmd run build`: passed.

未执行:

- Multi-tab browser stress test for duplicate SSE connection reduction.
# v1.8.5 Browser Smoke Status

- Browser Run-card and conversation refresh smoke is `not_run` for v1.8.5 in this environment because the production Docker stack was unavailable.
- Keep `BROWSER_AGENT_SMOKE_VERIFIED=not_run` until a real browser or Playwright run records run IDs, conversation IDs, artifacts, console output, and network/SSE behavior.

## meizhaiseek v1.8.7 Browser Core Smoke

已编码:

- Added optional Playwright smoke under `apps/web/e2e/agent-run-smoke.spec.ts`.
- The smoke uses environment-provided credentials and does not store passwords in code.
- The normal `npm.cmd run build` gate does not execute Playwright.

已执行:

- `npm.cmd run e2e:agent -- --project=chrome`: passed.
- Run `run_20260717094756_2c66e2b0` and conversation `conv_20260717094756_b1a833d3` validated real `/agent` submit, Run-card display, route conversation refresh, reload restore, failed terminal state, and user isolation.

未执行:

- Video Agent browser run with downloadable Excel/JSON/evidence.
- Cancel/retry UI flow.
- Browser DevTools-level SSE terminal-close timing.

Runtime marker:

- Keep `browser_agent_smoke_verified=failed` for v1.8.7 because the core smoke passed but the full browser matrix did not.
