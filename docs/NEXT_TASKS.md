# Next Tasks

当前版本：meizhaiseek v1.7

## v1.7.1：视频拆解蓝图迁移与发布闭环优化

目标：

- 在不改写 `video_script_workflow` 的前提下，继续验证 `bp_video_script_breakdown` 的测试用例、发布记录、回滚记录和 `/agent` 真实提交链路。
- 补充蓝图管理页的结构化输入预览和更细的版本 diff 展示。
- 增强导入冲突处理和测试结果摘要展示。

验收标准：

- 视频拆解蓝图保持 `published`。
- 8001 不可达时蓝图测试真实 FAIL；8001 可达时生成真实 run_id 和 artifacts。
- `/agent`、`/chat`、Dataset、Connector、Debug Payload、用户管理继续正常。

## P0：回归并守住 `/agent` 真实任务链路

### P0.1 任务执行后左侧聊天记录必须新增并持久保存

目标：

- 用户在 `/agent` 智能体界面提交任务后，后端必须创建或更新 agent conversation。
- 左侧聊天记录必须出现真实记录。
- 会话必须写入 APP SQLite，不能只存在前端 state 或 localStorage。
- 用户隔离必须按 `user_id` 生效。

涉及文件：

- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/hooks/useAgentConversations.ts`
- `apps/api/routers/conversations.py`
- `apps/api/routers/agent_runs.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`
- `apps/api/services/service_events.py`

验收标准：

- `POST /api/agent-runs` 返回 `run_id` 和 `conversation_id`。
- `GET /api/conversations` 能看到新会话。
- SQLite `agent_conversations`、`agent_messages`、`agent_runs` 有对应记录。
- 刷新页面后记录仍存在。
- 用户 A 不能看到用户 B 的会话。

### P0.2 切换路由再回来，任务和聊天不能消失

目标：

- 从 `/agent` 切到 `/chat`、`/board` 或其他路由，再回 `/agent`，恢复 active conversation、messages、latest run、status、result preview。
- 刷新页面也能恢复。
- localStorage 只保存 active conversation id，不保存完整 messages。

涉及文件：

- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/hooks/useAgentRunEvents.ts`
- `apps/web/src/hooks/useAgentRunPolling.ts`
- `apps/web/src/components/AgentWorkspace.tsx`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`

验收标准：

- 恢复优先级：URL `conversation_id` -> localStorage active id -> 空状态。
- running run 恢复后继续 SSE 或 polling。
- completed/failed/cancelled 不再重复轮询。
- 不存在或已归档 conversation 不白屏，显示中文空状态并清理无效 active id。
- 快速切换会话最终显示最后一次点击的会话。

### P0.3 脚本/视频拆解智能体提交后必须真实执行

目标：

- 视频拆解提交后只调用平台后端 `POST /api/agent-runs`。
- 后端根据 `agent_type=video_script_breakdown` 进入 `video_script_workflow`。
- 8001 未启动时任务真实 failed，不伪造成 completed。
- 8001 可达时真实 POST `/run`，保存 request/response Debug Payload 和 artifacts。

涉及文件：

- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/api/workflows/video_script_workflow.py`
- `apps/api/services/video_agent_payload_builder.py`
- `apps/api/services/local_agent_client.py`
- `apps/api/services/video_breakdown_result_normalizer.py`
- `apps/api/services/artifact_service.py`
- `apps/api/scripts/smoke_minimal.py`

验收标准：

- Payload 使用 `video_file`、`output_dir`、`subtitle_region`、`ocr_workers`。
- `standard` / `shot_text_excel` 最终映射为 `shot_text_excel`。
- 8001 不可达时 run.status 为 `failed`，错误信息清楚。
- 8001 可达时 run 能进入 running/completed，result_json 和 artifacts 持久化。
- Debug Payload request 是真实发给 8001 的 `/run` payload。

### P0.4 状态、结果、错误必须回显到对应聊天记录

目标：

- `running/completed/failed/cancelled` 通过 `service_events` 同步到对应 conversation 的 assistant message。
- completed 显示 summary、files、download URL。
- failed 显示清晰中文错误。
- retry 追加新 user/assistant messages 和新 run id，不覆盖旧 run。

涉及文件：

- `apps/api/services/service_events.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`
- `apps/web/src/components/AgentWorkspace.tsx`
- `apps/web/src/components/AgentRunStatus.tsx`
- `apps/web/src/components/VideoBreakdownResultPanel.tsx`

验收标准：

- running 状态能在聊天记录中看到任务进行中。
- completed 后对应 assistant message 显示结果摘要。
- failed 后对应 assistant message 显示错误摘要。
- cancelled 后显示任务已取消。
- 多会话、多 run 并存时状态不串线。

## P1：回归测试与 UI 稳定

### P1.1 前端 UI 不再因乱码或热编译状态掉页

目标：

- active docs、README、前端源码保持 UTF-8。
- `/agent`、`/chat`、后台面板 build 和运行时都不白屏。
- 视频结果 tab 不闪屏，长文本可查看完整内容。

涉及文件：

- `apps/web/src/components/VideoBreakdownResultPanel.tsx`
- `apps/web/src/components/ArtifactList.tsx`
- `apps/web/src/components/AdminConsolePanel.tsx`
- `docs/*.md`
- `README.md`

验收标准：

- `npm.cmd run build` 通过。
- `/agent` 返回 200。
- 乱码扫描 active docs 和 `apps/web/src` 无命中。
- 点击“镜头时间轴 / 字幕 OCR / 视觉证明帧 / 质量警告 / 输出文件”不闪屏。
- 长路径 hover 可看完整内容，横向滚动可查看全部文本。

### P1.2 保持测试链路可运行

目标：

- compileall、unittest、build 保持通过。
- smoke 缺凭据时清晰失败，不误报通过。
- 8001 E2E 可选执行，不影响默认 CI。

涉及文件：

- `apps/api/tests/*`
- `apps/api/scripts/smoke_minimal.py`
- `.github/workflows/ci.yml`
- `docs/SMOKE_TESTS.md`
- `docs/TESTING.md`

验收标准：

- `python -m compileall apps/api` 通过。
- `python -m unittest discover -s apps/api/tests` 通过。
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build` 通过。
- `python apps/api/scripts/smoke_minimal.py` 在缺凭据时返回非 0 并提示缺少凭据。

## P2：工程治理

### P2.1 日志与未跟踪文件治理

目标：

- 不提交 runtime、logs、uploads、models、node_modules、`.next`。
- 历史日志移动到 `apps/api/runtime/logs/archive/`，不删除非空日志。
- `ARCHITECTURE_EVALUATION_REPORT.md` 若只是参考资料，不提交。

涉及文件：

- `.gitignore`
- `start-dev.ps1`
- `start-dev.bat`
- `apps/api/runtime/logs/`
- `apps/api/api-8000.log.*`
- `apps/web/web-3000.log.*`

验收标准：

- `git status --short` 不出现敏感或 runtime 数据。
- 日志目录仍写入 `apps/api/runtime/logs/api-dev.log` 和 `web-dev.log`。
- 非空历史日志如需归档，保留文件内容。

### P2.2 文档保持可读并同步真实版本

目标：

- `AGENTS.md`、`docs/CODEX_HANDOFF.md`、`docs/NEXT_TASKS.md`、`docs/CHANGELOG_CONTEXT.md` 保持 UTF-8。
- 文档版本与 runtime health 保持 v1.7。
- 不把 archive 里的历史备份当当前文档来源。

涉及文件：

- `AGENTS.md`
- `docs/CODEX_HANDOFF.md`
- `docs/NEXT_TASKS.md`
- `docs/CHANGELOG_CONTEXT.md`
- `docs/API.md`
- `docs/PRD.md`

验收标准：

- active docs 乱码扫描无命中。
- `/api/admin/runtime/health` 返回 `version=v1.7`。
- 新窗口可以只靠交接文档接手项目。
