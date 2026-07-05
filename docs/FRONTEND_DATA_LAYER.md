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
