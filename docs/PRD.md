# 产品说明 PRD

## meizhaiseek v1.8.6

- Version focus: business queue closure, MinIO artifact storage acceptance, pgvector non-empty migration/resume, browser Agent smoke, and runtime marker closeout.
- Model display name remains `meizhaiseek 2.0`.
- No new business agents, v1.9 upgrade, local video Agent refactor, or local video Agent Prompt change are introduced in v1.8.6.
- 200/300/500-user capacity validation remains out of scope for v1.8.6 and must stay `not_run`.

## meizhaiseek v1.8.4

- Version focus: video Agent E2E acceptance, distributed queue closure, storage/pgvector validation, and honest capacity reporting.
- Model display name remains `meizhaiseek 2.0`.
- No new business agents, v1.9 upgrade, local video Agent refactor, or local video Agent Prompt change are introduced in v1.8.4.
- P0-P4 acceptance items remain `not_run` until real commands and evidence are recorded.

## meizhaiseek v1.8.3

- Version focus: full type gate, queue closure, pgvector validation, and production acceptance hardening.
- Model display name remains `meizhaiseek 2.0`.
- No new business agents are introduced in v1.8.3.
- 500-user validation remains not executed unless recorded separately with real Locust results.

## 当前版本

- 版本：meizhaiseek v1.8

## v1.8：500 用户并发扩展与分布式生产架构

v1.8 将平台从单机本地部署拓展到可生产扩展的架构基线：本地开发继续默认 SQLite、memory events、inline queue 和 local artifacts；生产推荐 PostgreSQL、Redis、RQ workers、分布式 SSE wakeup 和共享 artifact storage。模型展示名继续为 meizhaiseek 2.0。

## v1.7.2：智能体蓝图发布闭环与可视化配置增强

v1.7.2 在 v1.7 智能体蓝图基础能力上，补齐结构化配置、测试历史、验证历史、版本差异、发布门禁、预览和回滚确认能力。该版本将蓝图中心从 JSON 配置工具升级为可编辑、可验证、可测试、可发布、可回滚的完整管理闭环，同时继续保持 Blueprint 只描述和管理现有 Agent Registry、Workflow 与 Connector，不进行任意动态代码执行。
- 名称：智能体蓝图与方法论配置中心
- 模型展示名：meizhaiseek 2.0

## 项目目标

meizhaiseek-platform 是面向电商经营场景的本地轻量 AI 平台。平台通过统一 Agent Run 任务中心，把 AI 对话、知识库、Dataset、Connector、Debug Payload、视频拆解智能体和后台管理串成一个可本地部署、可审计、可恢复的工作台。v1.7 在现有 Agent Registry、Workflow 和 Connector 之上新增蓝图描述层，用于统一管理智能体方法论、输入输出协议、Prompt 配置、执行绑定、测试用例、发布和回滚。

## 架构原则

- 小团队本地部署优先，生产扩展路径明确。
- APP SQLite 与 RAG SQLite 分离，不合并边界；生产 APP 数据推荐 PostgreSQL。
- Redis 只用于 cache、rate limit、queue 和 event bus，业务真相仍在数据库。
- 前端统一通过 `apps/web/src/lib/api.ts` 调用后端。
- 读取型接口逐步接入 SWR；提交、删除、上传和下载仍走显式 API 调用。
- `/chat` 流式问答稳定优先。
- `/agent` run 状态优先 SSE，失败后回退轻量轮询。

## 核心模块

### AI 对话

支持首屏问答、RAG 检索、知识库入库、本地模型状态诊断、非流式问答和 SSE 流式输出。会话和消息持久化到 APP SQLite，RAG 文档和向量数据保存在独立 RAG SQLite。

### AI 智能体

支持智能体选择、技能模板、文件输入、Dataset 输入、Connector 调用、任务取消、重试、下载、Debug Payload、会话恢复和状态回写。

### 智能体蓝图

支持蓝图草稿、测试中、已发布、已停用和已废弃生命周期；支持版本历史、输入协议、方法论步骤、Prompt 模板、执行配置、输出协议、结果 UI 配置、测试用例、验收规则、复制、导入、导出、发布与回滚。蓝图是现有运行时能力的配置描述层，不替代 Agent Registry，也不动态执行任意 JSON 代码。

### 视频拆解智能体

平台通过 Connector 调用本地 8001 视频 Agent。任务会生成真实 `/run` payload，保存 Debug Payload，标准化 completed 结果，登记 Excel、shot report、图片和 folder manifest artifacts，并在前端结果面板恢复展示。

### Dataset

支持上传表格、字段识别、字段映射、清洗、结果文件管理和 SQLite metadata 持久化。文件本体仍保存在磁盘。

### 后台管理

支持用户管理、角色控制、审计日志、运行时健康检查、storage health、Connector 管理、Debug Payload 查看和 replay。

## 版本路线

- v1.5.2：AI 对话首屏问答功能。
- v1.5.3：AI 对话知识库入库与 RAG 管理中心。
- v1.5.4：会话栏交互优化。
- v1.5.5：本地模型状态与 RAG 可用性诊断。
- v1.5.6：AI 对话流式输出。
- v1.5.7：文档乱码修复与 APP SQLite 迁移。
- v1.5.8：增量 upsert、Dataset SQLite、service_events。
- v1.6：视频拆解智能体生产化。
- v1.6.1：AI 智能体会话切换稳定性修复。
- v1.6.2：AI 智能体页面卡顿深度优化。
- v1.6.3：架构评估 P1-P3 优化与工程规范补齐。
- v1.6.4：视频拆解智能体真实成功链路验收与产物闭环。
- v1.6.5：架构评估 P1-P3 二轮优化、回归测试与服务启动。
- v1.7：智能体蓝图与方法论配置中心。
- v1.8：500 用户并发扩展与分布式生产架构。

## v1.8 说明

v1.8 新增 SQLAlchemy/Alembic/PostgreSQL 生产 schema、SQLite 到 PostgreSQL 迁移脚本、Redis 服务、登录限流、RQ/inline queue facade、Agent Run Redis Pub/Sub 事件总线、artifact storage provider、RAG provider facade、request id/metrics middleware、Docker production topology 和 Locust 基线脚本。500 用户结果必须以真实 Locust 报告为准；资源不足时只记录“未执行”。

## v1.7 说明

v1.7 将平台从单独开发智能体功能升级为统一管理智能体方法论的配置平台。该版本新增智能体蓝图、版本管理、输入协议、方法论步骤、Prompt 模板、执行绑定、输出协议、结果页面配置、测试用例、验收规则、发布、回滚、复制和导入导出能力。视频拆解智能体作为第一份正式蓝图接入，但继续沿用原有稳定工作流和 8001 Connector，不进行动态工作流重写。

## v1.6.5 说明

v1.6.5 根据 2026-07-01 架构评估报告继续处理 P1-P3 优化项。该版本扩大 SWR 数据层覆盖范围，增加 auth、conversation、agent-runs、video normalizer 等核心路径测试；治理残留日志与 legacy JSON fallback；补充 Docker Compose 生产模式；新增 SQLite async wrapper 第一阶段；新增 Agent Run SSE 状态推送并保留 polling fallback；强化视频拆解 E2E 测试，提升工程稳定性、可维护性和本地部署可靠性。


## meizhaiseek v1.7.2

v1.7.2 focuses on architecture stabilization after the 2026-07-03 evaluation: Blueprint release E2E coverage, wider auth/conversation/task tests, Blueprint Store splitting, legacy JSON fallback retirement diagnostics, production Docker build/start, Agent Run SSE tests, async SQLite read wrappers, frontend API module compatibility split, methodology drag ordering, Registry/Blueprint reconciliation, and the Agent Run Event Hub. Existing Agent, Workflow, Connector, APP SQLite, RAG SQLite, Dataset, QA/RAG, Debug Payload, and video breakdown execution models are unchanged.
