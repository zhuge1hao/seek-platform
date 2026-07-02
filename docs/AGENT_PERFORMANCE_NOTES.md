# Agent Performance Notes

## 当前策略

- `/agent` 会话列表通过 SWR 读取，但不高频刷新。
- run 状态优先使用 `GET /api/agent-runs/{run_id}/events` SSE。
- SSE 失败后回退到 `useAgentRunPolling`。
- run summary/result 不交给 SWR 轮询，避免双重请求。
- 大 result、Debug Payload、artifact 详情按需加载。

## v1.6.5 边界

- SWR 适合稳定 GET/list/detail。
- POST、PUT、DELETE、上传、下载、replay、任务提交仍走显式 API。
- 成功写入后调用对应 SWR `mutate`。
- 视频拆解 completed 后，结果恢复依赖 APP SQLite 中的 run、conversation、artifact metadata。

## 排查建议

- UI 白屏先看 `apps/api/runtime/logs/web-dev.log`。
- API 问题先看 `apps/api/runtime/logs/api-dev.log`。
- Agent 卡住先查 SSE，再查 summary polling，再查 run status 和 service_events。
