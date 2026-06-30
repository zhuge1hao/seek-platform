# Next Tasks

当前目录没有 `.git` 元数据。下一窗口必须直接读取磁盘文件确认现状，不要依赖 git diff。

## P0：回归并补齐 `/agent` 会话持久化和真实任务链路

### P0.1 `/agent` 执行任务后左侧聊天记录必须新增并持久保存

目标：

- 用户在 `/agent` 提交任意智能体任务后，后端创建或更新 agent conversation。
- 左侧二级会话栏立即出现真实记录。
- 会话按 `user_id` 隔离，写入 APP SQLite 主存储。
- 不允许只存在前端 state 或 localStorage。

涉及文件：

- `apps/api/routers/agent_runs.py`
- `apps/api/routers/conversations.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`
- `apps/api/services/app_sqlite.py`
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/components/ConversationPanel.tsx`
- `apps/web/src/components/ConversationMessages.tsx`
- `apps/web/src/lib/api.ts`

验收标准：

- `POST /api/agent-runs` 返回 `conversation_id`。
- `GET /api/conversations` 能看到新会话。
- SQLite `agent_conversations` / `agent_messages` 有对应记录。
- 用户 A 不能看到用户 B 的 agent conversation。
- 刷新页面后记录仍存在。

### P0.2 切换到其他路由再回来，任务/聊天不能消失

目标：

- 从 `/agent` 切到 `/chat`、`/board`、`/competition-diagnosis` 等路由，再回 `/agent`，恢复当前会话、messages、latest run、状态和结果。
- 刷新页面也能恢复。

涉及文件：

- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/components/AgentRunStatus.tsx`
- `apps/web/src/components/GenericAgentPanel.tsx`
- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/web/src/lib/api.ts`
- `apps/api/routers/conversations.py`

验收标准：

- 恢复优先级为 URL `conversation_id` → `localStorage.meizhaiseek_active_conversation_id` → 空首页。
- localStorage 只保存 active ID，不保存完整会话数据。
- running run 恢复后继续轮询。
- completed/failed/cancelled 不再轮询。
- archived 或不存在的 conversation 显示中文空状态或 warning，不白屏。

### P0.3 脚本拆解智能体必须真实执行，而不是只创建 UI 状态

目标：

- 视频脚本拆解提交后只调用 `POST /api/agent-runs`。
- 后端 Orchestrator 根据 `agent_type=video_script_breakdown` 进入 `video_script_workflow`。
- local agent 8001 未启动时，任务必须真实 failed，不能伪造成 completed。

涉及文件：

- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/api/routers/agent_runs.py`
- `apps/api/services/orchestrator.py`
- `apps/api/workflows/video_script_workflow.py`
- `apps/api/services/local_agent_client.py`
- `apps/api/services/agent_connector_store.py`
- `.env.example`

验收标准：

- payload 保留 `video_path`、`video_url`、`agent_type=video_script_breakdown`。
- 固定 session ID 为 `019dd824-f4bb-7273-8ac3-6e19b195ff82`。
- 8001 不可达时 run 和对应 assistant message 均为 failed，并写入清晰中文错误。
- 如果有真实 local agent，Debug Payload 能看到 request/response。

### P0.4 任务状态、结果、错误信息要回显到对应聊天记录

目标：

- `running/completed/failed/cancelled` 同步到对应 conversation 的 assistant message。
- retry 沿用同一 conversation，追加新的 user/assistant 消息和新 run ID。
- 错误和结果不能串到其他会话。

涉及文件：

- `apps/api/services/task_store.py`
- `apps/api/services/conversation_store.py`
- `apps/api/routers/agent_runs.py`
- `apps/web/src/components/AgentRunStatus.tsx`
- `apps/web/src/components/ConversationMessages.tsx`
- `apps/web/src/app/agent/page.tsx`

验收标准：

- completed 消息保留 result、files、download URL。
- failed 消息展示简明中文错误。
- cancelled 消息展示“任务已取消”。
- 多会话、多 run 并存时状态不串线。

## P1：SQLite 迁移后的回归验证

### P1.1 登录、权限、用户隔离回归

目标：

- 确认 APP SQLite 替换 JSON 后，登录、角色权限、`auth_version`、用户启用/禁用仍正确。

涉及文件：

- `apps/api/services/user_store.py`
- `apps/api/services/audit_log_service.py`
- `apps/api/routers/auth.py`
- `apps/api/routers/admin_users.py`

验收标准：

- admin/operator/viewer 可按预期登录。
- 禁用用户不能继续使用旧 token。
- 重置密码后旧 token 失效。
- 最后一个启用 admin 不能被禁用。

### P1.2 APP SQLite storage health 和手动迁移回归

目标：

- 确认 storage health 可用，手动迁移幂等，不重复膨胀计数。

涉及文件：

- `apps/api/routers/admin_runtime.py`
- `apps/api/services/app_sqlite.py`
- `apps/api/services/json_to_sqlite_migrator.py`

验收标准：

- `GET /api/admin/storage/health` admin 返回 200。
- 未登录返回 401，非 admin 返回 403。
- `POST /api/admin/storage/migrate-json` 可重复执行。
- 旧 JSON 不被删除，legacy backup 目录存在。

## P2：文档与轻量 smoke

### P2.1 文档同步

目标：

- 保持 `docs/API.md`、`docs/PRD.md`、`docs/TODO.md`、`docs/CODEX_HANDOFF.md` 与实际接口一致。

涉及文件：

- `docs/API.md`
- `docs/PRD.md`
- `docs/TODO.md`
- `docs/CODEX_HANDOFF.md`
- `docs/CHANGELOG_CONTEXT.md`

验收标准：

- v1.5.6 明确是“AI 对话流式输出与回答体验优化”。
- v1.5.7 明确是“文档乱码修复与 SQLite 存储底座迁移”。
- 没有常见 mojibake 乱码标记。

### P2.2 最小自动化 smoke

目标：

- 留下最小可重复检查，不引入大测试框架。

建议覆盖：

- `/health`
- 登录 admin
- `/api/admin/runtime/health`
- `/api/admin/storage/health`
- `/api/qa/conversations`
- `/api/conversations`
- `/api/qa/model-status`

验收标准：

- `python -m compileall apps/api` 通过。
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build` 通过。
- smoke 步骤写入文档或保留一个轻量脚本。
