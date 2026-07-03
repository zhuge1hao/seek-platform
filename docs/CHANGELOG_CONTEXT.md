# Changelog Context

## 当前状态

- 当前版本：meizhaiseek v1.7
- 当前分支：main
- 最近提交：`dd1a9e9 fix: restore UI docs encoding`
- 本轮新增能力：智能体蓝图与方法论配置中心、视频拆解样板蓝图、蓝图测试/发布/回滚/导入导出。

## v1.7：智能体蓝图与方法论配置中心

完成内容：

- 新增 `agent_blueprints`、`agent_blueprint_versions`、`agent_blueprint_test_cases`、`agent_blueprint_releases`。
- 新增蓝图 store、service、validator、import/export、seed service。
- 新增 `/api/agent-blueprints` 全套 CRUD、versions、validate、publish、rollback、clone、disable/enable/deprecate、test-cases、releases、export/import API。
- `/api/agents` 返回蓝图关联字段，无蓝图智能体保持 `unmanaged`。
- `POST /api/agent-runs` 仅在关联蓝图为 disabled/deprecated 时拒绝新任务。
- 视频拆解智能体 seeded 为第一份 published 蓝图，继续绑定 `video_script_workflow`、`video_script_agent` 和 `video_breakdown` renderer。
- 后台管理新增“智能体蓝图”入口，支持列表、详情、JSON 编辑、验证、测试、发布、回滚、复制、导入导出。
- 新增自动化测试覆盖 store、service、validator、import/export、API 权限。
- runtime health 和前端展示升级为 `meizhaiseek v1.7`，模型名继续 `meizhaiseek 2.0`。

## v1.6.5：架构评估 P1-P3 二轮优化、回归测试与服务启动

完成内容：

- 扩大 SWR 读取层覆盖，新增多个读取型 hooks。
- 新增核心 unittest，覆盖 auth、conversation、task_store、agent-runs API、video normalizer。
- `APP_LEGACY_JSON_FALLBACK=false` 默认关闭。
- runtime health 增加 `legacy_json_fallback_enabled`。
- 新增 Docker production compose。
- 新增 SQLite async wrapper 第一阶段。
- 新增 Agent Run SSE events 接口，前端失败回退 polling。
- 增强 video-agent E2E smoke。
- 修复视频结果 tab 闪屏。
- 修复视频结果长文本截断查看体验。
- 修复 active docs 和 README 乱码。

关键提交：

- `5c0fc25 chore: address architecture P1-P3 follow-up items`
- `412b68e fix: reveal long video result text`
- `db35e66 fix: prevent video result tab flicker`
- `845b4bc fix: keep next dev assets stable during build`
- `dd1a9e9 fix: restore UI docs encoding`

## v1.6.4：视频拆解智能体真实成功链路验收与产物闭环

完成内容：

- 默认 Connector 修正到本地 8001。
- `GET /api/agents/video-script/status` 请求 `/health`，返回 connected/disconnected，不可达不 500。
- 新增视频 Agent payload builder，把平台字段映射为本地 `/run` payload。
- 真实 POST `/run`，不伪造 completed。
- 标准化 result_json.summary，兼容 raw shot count、optimized shots、Excel columns/images、Excel path、shot report path。
- 读取 shot_report JSON，提取 timeline 和 proof frames。
- 收集 Excel、JSON、TXT、MD、PNG、JPG、WEBP artifacts。
- 生成 folder_manifest，artifact metadata 写入 APP SQLite。
- 前端结果面板展示 completed summary、steps、tabs、输出文件。
- Debug Payload 保存真实 request/response/error。
- smoke 增加 `--video-agent-e2e` 和 `--require-video-agent`。

## v1.6.3：架构评估 P1-P3 优化与工程规范补齐

完成内容：

- 引入 SWR 基础数据层。
- DeepSeek 非流式调用增加 `async_generate_answer` wrapper。
- 新增 smoke 脚本和 docs。
- 日志目录治理。
- 历史 `.bak-v1.5.7` 文档归档。
- 新增安全配置生成式初始化。
- 补充 Docker Compose 和 GitHub Actions CI。

## v1.6.2：AI 智能体页面卡顿深度优化

完成内容：

- 拆分 run summary/result。
- 大 result/debug payload 延迟加载。
- 快速切换 conversation 过期请求忽略。
- `/agent` 单一 run polling 边界。

## v1.6.1：AI 智能体会话切换稳定性修复

完成内容：

- `/agent?conversation_id=` 切换增加 AbortController。
- URL 与 activeConversationId 同步修复。
- 切换路由和刷新恢复会话。

## v1.6：视频拆解智能体生产化

完成内容：

- 新增视频拆解智能体专用面板。
- 新增 local agent status check。
- 视频任务标准 steps、result_json、artifact、Debug Payload。
- 8001 不可达时任务真实 failed。

## v1.5.8：存储性能优化与 Dataset SQLite 统一

完成内容：

- QA conversation 和 Agent conversation 改为增量 upsert。
- Dataset metadata 迁入 APP SQLite。
- 新增 `datasets`、`dataset_files`、`dataset_jobs`。
- 新增 `service_events`，解除 task_store 与 conversation_store 的循环依赖。

## v1.5.7：文档乱码修复与 SQLite 存储底座迁移

完成内容：

- 新增 APP SQLite 初始化、迁移和 health。
- 用户、审计、QA conversation、Agent conversation、agent_runs、Connector、Debug Payload、files、artifacts metadata 迁入 APP SQLite。
- RAG SQLite 继续只保存 knowledge documents/chunks/embedding。

## v1.5.2-v1.5.6：AI 对话、知识库与流式问答

完成内容：

- AI 对话首屏问答。
- 知识库文档入库与 RAG 管理中心。
- 会话栏交互优化。
- 本地模型状态与 RAG 可用性诊断。
- `/chat` SSE 流式输出与回答体验优化。

## 下个窗口注意

- 第一优先级仍是 `/agent` 真实任务链路回归，不要被 UI 表象骗过去。
- 8001 不可达时必须 failed；8001 可达时必须真实 `/run`。
- smoke 缺 admin 凭据时失败是正常保护，不要改成默认通过。
- 未跟踪 `ARCHITECTURE_EVALUATION_REPORT.md` 不要误提交。
