# Next Tasks

当前版本：meizhaiseek v1.6.5

## P0 稳定性守护

- 确保 `/agent` 会话持久化、路由恢复、取消、重试、下载稳定。
- 确保 `/chat` SSE 流式问答不受智能体改动影响。
- 确保视频拆解任务不能伪造成功：8001 不可达必须 failed。
- 确保前端接口异常显示错误态，不白屏。

## P1 可维护性

- 继续扩大 SWR 到低风险读取型接口。
- 保持 `/agent` run 状态由 SSE 或 polling 负责，SWR 不重复轮询 run summary。
- 增加更多 service 层测试，优先覆盖失败分支。

## P2 运行治理

- 观察 `APP_LEGACY_JSON_FALLBACK=false` 后的生产运行情况。
- 清理不再使用的历史 JSON fallback 分支前，先保留备份和回退说明。
- 持续归档日志到 `apps/api/runtime/logs/archive/`。

## P3 后续优化

- SQLite async wrapper 先覆盖高频读取，避免一次性改动所有 store。
- 评估 SSE 稳定性，再逐步减少 polling 频率。
- 视频 Agent E2E 增加更多真实失败样例。
