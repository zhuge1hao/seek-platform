# Next Tasks

当前版本：`meizhaiseek v1.6.3`

本文件只描述下一窗口优先级。不要把前端 UI 状态当作后端成功；所有 P0 都必须落到真实 API、SQLite 持久化和会话回写。

## P0：回归并修复 `/agent` 任务执行、会话持久化和状态回写

### P0.1 执行任务后左侧聊天记录必须新增并持久保存

目标：

- 用户在 `/agent` 智能体界面提交任务后，后端必须创建或更新 agent conversation。
- 左侧会话栏必须出现真实记录。
- 会话必须写入 APP SQLite，不允许只存在前端 state 或 localStorage。
- 用户隔离必须按 `user_id` 生效。

涉及文件：

- `apps/api/routers/agent_runs.py`
- `apps/api/routers/conversations.py`
- `apps/api/services/task_store.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/service_events.py`
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/components/ConversationPanel.tsx`
- `apps/web/src/lib/api.ts`

验收标准：

- `POST /api/agent-runs` 返回 `run_id` 和 `conversation_id`。
- `GET /api/conversations` 能看到新会话。
- SQLite `agent_conversations` / `agent_messages` / `agent_runs` 有对应记录。
- 刷新页面后记录仍存在。
- 用户 A 不能看到用户 B 的会话。

### P0.2 切换路由再回来任务/聊天不能消失

目标：

- 从 `/agent` 切到 `/chat`、`/board` 或其他路由，再回 `/agent`，恢复 active conversation、messages、latest run、status、result preview。
- 刷新页面也能恢复。
- localStorage 只保存 active conversation id，不保存完整 messages。

涉及文件：

- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/hooks/useAgentRunPolling.ts`
- `apps/web/src/components/AgentRunStatus.tsx`
- `apps/web/src/components/GenericAgentPanel.tsx`
- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/web/src/lib/api.ts`
- `apps/api/routers/conversations.py`

验收标准：

- 恢复优先级：URL `conversation_id` -> `localStorage.meizhaiseek_active_conversation_id` -> 空状态。
- running run 恢复后继续轮询。
- completed/failed/cancelled 不再轮询。
- 不存在或已归档 conversation 不白屏，显示中文空状态并清理无效 active id。
- 快速切换会话最终显示最后一次点击的会话。

### P0.3 脚本拆解智能体提交后必须真实执行后端任务

目标：

- 视频脚本拆解提交后只调用平台后端 `POST /api/agent-runs`。
- 后端根据 `agent_type=video_script_breakdown` 进入 `video_script_workflow`。
- 8001 未启动时任务真实 failed，不伪造成 completed。
- 真实 local agent 存在时，保存 request/response Debug Payload 和 artifacts。

涉及文件：

- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/api/routers/agent_runs.py`
- `apps/api/services/orchestrator.py`
- `apps/api/workflows/video_script_workflow.py`
- `apps/api/services/local_agent_client.py`
- `apps/api/services/video_agent_status_service.py`
- `apps/api/services/debug_payload_service.py`
- `apps/api/services/artifact_service.py`

验收标准：

- payload 保留 `agent_type=video_script_breakdown`、mode、workflow_options、video_path/video_url。
- 默认 session id 继续沿用 `019dd824-f4bb-7273-8ac3-6e19b195ff82`。
- 8001 不可达时 run.status 为 `failed`，错误内容包含无法连接本地视频 Agent。
- failed run 写入 APP SQLite。
- 如果 8001 可达，run 能进入 running/completed，result_json 和 artifacts_json 持久化。

### P0.4 任务状态、结果、错误信息回显到对应聊天记录

目标：

- `running/completed/failed/cancelled` 通过 `service_events` 同步到对应 conversation 的 assistant message。
- completed 显示 summary、files、download URL。
- failed 显示清晰中文错误。
- retry 追加新 user/assistant messages 和新 run ID，不覆盖旧 run。

涉及文件：

- `apps/api/services/task_store.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/service_events.py`
- `apps/api/routers/agent_runs.py`
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/components/AgentRunStatus.tsx`
- `apps/web/src/components/ConversationMessages.tsx`

验收标准：

- running 状态能在聊天记录中看到任务进行中。
- completed 后对应 assistant message 显示结果摘要。
- failed 后对应 assistant message 显示错误摘要。
- cancelled 后显示任务已取消。
- 多会话、多 run 并存时状态不串线。

## P1：v1.6.2 性能链路回归

### P1.1 确认 `/agent` 仍只有单一 run polling

目标：

- 页面同一时间只有 `useAgentRunPolling.ts` 负责 active run 轮询。
- 子组件不再创建 `setInterval`。

涉及文件：

- `apps/web/src/hooks/useAgentRunPolling.ts`
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/components/GenericAgentPanel.tsx`
- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/web/src/components/AgentRunStatus.tsx`

验收标准：

- `rg "setInterval|polling|pollRun" apps/web/src` 没有重复轮询实现。
- running 轮询请求走 `/api/agent-runs/{run_id}/summary`。
- terminal 状态停止轮询。
- 连续失败 3 次停止轮询并显示错误。

### P1.2 确认大 payload 延迟加载

目标：

- conversation detail 不默认返回完整 result/debug payload。
- VideoBreakdownResultPanel 默认只渲染概览和摘要。
- 完整 result 只在用户展开相关 tab 时按需加载。

涉及文件：

- `apps/api/routers/conversations.py`
- `apps/api/routers/agent_runs.py`
- `apps/api/services/task_store.py`
- `apps/web/src/components/VideoBreakdownResultPanel.tsx`
- `apps/web/src/lib/api.ts`

验收标准：

- `GET /api/conversations/{conversation_id}` 返回 run/message preview，不返回完整 raw_response/debug payload。
- `GET /api/agent-runs/{run_id}/summary` 返回轻量摘要。
- `GET /api/agent-runs/{run_id}/result` 返回完整 result。
- timeline 首屏不超过 20 条，subtitles 不超过 30 条，proof_frames 不超过 20 条，files 不超过 30 条。

## P2：文档、GitHub 和最小 smoke

### P2.1 保持文档同步

目标：

- 文档和真实版本 v1.6.3 保持一致。
- 不再出现乱码交接文档。

涉及文件：

- `AGENTS.md`
- `docs/CODEX_HANDOFF.md`
- `docs/NEXT_TASKS.md`
- `docs/CHANGELOG_CONTEXT.md`
- `docs/API.md`
- `docs/PRD.md`
- `docs/TODO.md`

验收标准：

- `docs/CODEX_HANDOFF.md` 能让新窗口直接接手。
- `docs/NEXT_TASKS.md` P0/P1/P2 清晰。
- `docs/CHANGELOG_CONTEXT.md` 记录 v1.5.7 到 v1.6.3。
- 禁止词扫描无命中：旧品牌词、旧个人称呼、额度展示文案、试用/演示类文案都不能出现。

### P2.2 最小自动化 smoke

目标：

- 不引入大测试框架，保留最小可重复检查。

建议覆盖：

- `/health`
- 登录 admin
- `/api/admin/runtime/health`
- `/api/admin/storage/health`
- `/api/conversations`
- `/api/agent-runs/{run_id}/summary`
- `/api/qa/model-status`

验收标准：

- `python -m compileall apps/api` 通过。
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build` 通过。
- smoke 结果记录到交接说明或 TODO。

### P2.3 GitHub 同步

目标：

- 本地改动完成并验证后同步到 GitHub。

涉及文件：

- 全项目 Git 状态。

验收标准：

- `git status -sb` 清楚。
- 不提交 `.env`、runtime、SQLite、uploads、models、logs、node_modules、`.next`。
- 推送到 `https://github.com/zhuge1hao/seek-platform.git`。
