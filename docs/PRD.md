# 产品说明 PRD

## 当前版本

- 版本：meizhaiseek v1.6.5
- 名称：架构评估 P1-P3 二轮优化、回归测试与服务启动
- 模型展示名：meizhaiseek 2.0

## 项目目标

meizhaiseek-platform 是面向电商经营场景的本地轻量 AI 平台。平台通过统一 Agent Run 任务中心，把 AI 对话、知识库、Dataset、Connector、Debug Payload、视频拆解智能体和后台管理串成一个可本地部署、可审计、可恢复的工作台。

## 架构原则

- 小团队本地部署优先。
- APP SQLite 与 RAG SQLite 分离，不合并边界。
- 不新增外部数据库服务。
- 前端统一通过 `apps/web/src/lib/api.ts` 调用后端。
- 读取型接口逐步接入 SWR；提交、删除、上传和下载仍走显式 API 调用。
- `/chat` 流式问答稳定优先。
- `/agent` run 状态优先 SSE，失败后回退轻量轮询。

## 核心模块

### AI 对话

支持首屏问答、RAG 检索、知识库入库、本地模型状态诊断、非流式问答和 SSE 流式输出。会话和消息持久化到 APP SQLite，RAG 文档和向量数据保存在独立 RAG SQLite。

### AI 智能体

支持智能体选择、技能模板、文件输入、Dataset 输入、Connector 调用、任务取消、重试、下载、Debug Payload、会话恢复和状态回写。

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

## v1.6.5 说明

v1.6.5 根据 2026-07-01 架构评估报告继续处理 P1-P3 优化项。该版本扩大 SWR 数据层覆盖范围，增加 auth、conversation、agent-runs、video normalizer 等核心路径测试；治理残留日志与 legacy JSON fallback；补充 Docker Compose 生产模式；新增 SQLite async wrapper 第一阶段；新增 Agent Run SSE 状态推送并保留 polling fallback；强化视频拆解 E2E 测试，提升工程稳定性、可维护性和本地部署可靠性。
