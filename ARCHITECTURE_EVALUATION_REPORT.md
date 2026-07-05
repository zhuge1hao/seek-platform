# meizhaiseek-platform 项目架构评估与项目评估报告

> **评估日期**：2026-07-03
> **当前版本**：v1.7.1
> **评估方式**：静态代码分析 + 结构审查 + 依赖审计 + 文档核对
> **评估人**：Claude Code 架构分析

---

## 一、项目概述

### 1.1 项目定位

**meizhaiseek-platform** 是一个面向**电商经营全链路的 AI 智能分析平台**，定位为可登录、可审计、可恢复的本地工作台。核心能力包括：

- **AI 智能体任务中心** — 多智能体统一任务提交、轮询、取消、重试
- **AI 对话（RAG 问答）** — 基于知识库的 DeepSeek 流式问答
- **知识库管理** — 文档入库、向量化、检索
- **电商数据清洗** — Excel 字段映射、重复/费比清洗
- **视频拆解智能体** — 本地视频脚本结构化拆解（已生产化）
- **智能体蓝图中心** — 方法论配置、版本管理、测试运行、发布门禁（v1.7 新增）
- **后台管理** — 账号治理、审计日志、Connector 联调

### 1.2 目标用户

小团队本地部署场景，设计容量 **< 50 并发用户**，不依赖任何外部数据库或中间件。

### 1.3 代码规模

| 模块 | 文件数 | 代码行数 |
|------|--------|----------|
| 后端 Python | 88 文件（16 routers + 63 services + 7 workflows + 6 steps + 3 schemas + 3 其他） | ~12,182 LOC |
| 前端 TypeScript/TSX | 79 文件（8 pages + 1 layout + 31 components + 7 ui + 16 hooks + 8 lib） | ~6,726 LOC |
| **合计** | **~167 源文件** | **~18,908 LOC** |

> 对比 v1.6.4：后端 +2,901 LOC（+31%），前端 +1,064 LOC（+19%），总文件数 +20。增长主要来自蓝图中心（8 个 service + 1 个 router + 2 个组件 + 11 个测试文件）。

---

## 二、技术栈总览

| 层级 | 技术选型 | 版本 |
|------|----------|------|
| **前端框架** | Next.js (App Router) + React | 14.2.23 + 18.3.1 |
| **前端样式** | Tailwind CSS + Lucide React | 3.4.17 + 0.468 |
| **前端数据层** | SWR (stale-while-revalidate) | 2.4.2 |
| **前端语言** | TypeScript | 5.7.2 |
| **后端框架** | FastAPI + Uvicorn | 0.115.6 + 0.34.0 |
| **数据校验** | Pydantic (FastAPI 内置) | — |
| **主存储** | SQLite 3 (WAL 模式) | stdlib `sqlite3` |
| **向量存储** | SQLite 3 (独立实例) | stdlib `sqlite3` |
| **AI 推理** | DeepSeek API | deepseek-v4-flash |
| **向量模型** | BGE-small-zh (sentence-transformers) | 3.3.1 |
| **表格处理** | openpyxl + xlrd | 3.1.5 + 2.0.1 |
| **文档解析** | python-docx | 1.1.2 |
| **HTTP 客户端** | requests | 2.32.3 |
| **文件上传** | python-multipart | 0.0.20 |
| **测试框架** | unittest + pytest | stdlib + 8.3.4 |
| **认证** | PBKDF2 + HMAC JWT | 自实现 |
| **语言** | Python 3.12 + TypeScript 5.7 | — |
| **包管理** | pip + npm | — |
| **容器** | Docker + Docker Compose | — |
| **CI** | GitHub Actions | — |

**依赖极简**：后端仅 **9 个** pip 依赖（v1.6.4 为 8 个，新增 `pytest`），前端仅 **5 个** npm 生产依赖（Next.js / React / React-DOM / Lucide / SWR）。

---

## 三、项目结构

```
meizhaiseek-platform/
|-- apps/
|   |-- api/                          # FastAPI 后端
|   |   |-- main.py                   (76 LOC) 入口：加载 .env → 初始化 SQLite → 注册路由 → 启动迁移 → 种子蓝图
|   |   |-- routers/     (16 个文件)  # HTTP 路由层
|   |   |   |-- admin_runtime.py      # 运行时健康检查、配置备份/修复/重置
|   |   |   |-- admin_users.py        # 管理员账号 CRUD
|   |   |   |-- agent_blueprints.py   # 智能体蓝图中心（v1.7 新增，288 LOC）
|   |   |   |-- agent_configs.py      # 智能体配置管理
|   |   |   |-- agent_connectors.py   # 本地 Agent Connector 管理
|   |   |   |-- agent_runs.py         # 任务创建/查询/取消/重试/summary/result/preview-payload
|   |   |   |-- agents.py             # 智能体列表/状态
|   |   |   |-- artifacts.py          # 产物下载/预览
|   |   |   |-- auth.py               # 登录/改密/当前用户
|   |   |   |-- chat.py               # 聊天路由
|   |   |   |-- conversations.py      # 会话列表/详情/归档/重命名
|   |   |   |-- datasets.py           # 数据集 CRUD/清洗/导出
|   |   |   |-- files.py              # 文件上传/预览/列表
|   |   |   |-- qa_chat.py            # AI 问答（非流式 + SSE 流式）
|   |   |   |-- qa_knowledge.py       # 知识库文档管理
|   |   |   |-- skills.py             # 技能模板管理
|   |   |
|   |   |-- services/    (63 个文件)   # 业务逻辑层
|   |   |   |-- app_sqlite.py         # SQLite 连接管理（WAL 模式）
|   |   |   |-- app_sqlite_migrations.py  # 建表迁移（22 张表 + 27 个索引）
|   |   |   |-- json_to_sqlite_migrator.py # JSON → SQLite 迁移器
|   |   |   |-- async_store_utils.py  # 异步 SQLite 操作包装（v1.7 新增）
|   |   |   |-- legacy_json_fallback.py  # 旧 JSON fallback 开关（v1.7 新增）
|   |   |   |-- task_store.py         # agent_runs 读写（283 LOC）
|   |   |   |-- conversation_store.py # agent_conversations/messages 读写（406 LOC 最复杂）
|   |   |   |-- qa_conversation_store.py  # QA 会话读写（369 LOC）
|   |   |   |-- dataset_store.py      # 数据集元数据读写（330 LOC）
|   |   |   |-- user_store.py         # 用户账号读写
|   |   |   |-- audit_log_service.py  # 审计日志
|   |   |   |-- auth_service.py       # PBKDF2 密码校验
|   |   |   |-- token_service.py      # HMAC JWT 签发/验证
|   |   |   |-- orchestrator.py       # 工作流分发调度
|   |   |   |-- deepseek_client.py    # DeepSeek API 客户端（含流式 + async）
|   |   |   |-- local_agent_client.py # 本地 Agent HTTP/CLI 调用
|   |   |   |-- qa_embedding_service.py   # BGE 向量生成
|   |   |   |-- qa_rag_retriever.py   # RAG 向量检索
|   |   |   |-- qa_rag_store.py       # RAG SQLite 读写
|   |   |   |-- qa_stream_service.py  # SSE 流式问答编排
|   |   |   |-- service_events.py     # 轻量事件钩子（解耦循环依赖）
|   |   |   |-- debug_payload_service.py  # Debug Payload 记录/查询
|   |   |   |-- artifact_service.py   # 产物文件管理
|   |   |   |-- file_store.py         # 文件元数据读写
|   |   |   |-- data_cleaning_service.py  # 电商数据清洗
|   |   |   |-- field_mapping_service.py  # 字段映射建议
|   |   |   |-- config_backup_service.py  # 配置备份/修复/重置
|   |   |   |-- config_guard.py       # 配置校验守卫
|   |   |   |-- config_migration_service.py  # 配置迁移
|   |   |   |-- agent_run_maintenance.py  # Zombie 任务回收
|   |   |   |-- video_agent_status_service.py  # 视频 Agent 连接状态
|   |   |   |-- video_agent_payload_builder.py  # 视频 Agent 载荷构建
|   |   |   |-- video_breakdown_result_normalizer.py  # 视频拆解结果规范化
|   |   |   |-- security_config_service.py  # 安全配置：secret 生成 + 密码策略 + warnings
|   |   |   |-- payload_preview_service.py  # Payload 预览构建
|   |   |   |-- agent_connector_store.py  # Connector 存储
|   |   |   |-- agent_connector_tester.py  # Connector 连接测试
|   |   |   |-- agent_config_store.py  # Agent 配置存储
|   |   |   |-- agent_registry.py     # Agent 注册表
|   |   |   |-- agent_protocol_parser.py  # Agent 协议解析
|   |   |   |-- password_service.py   # 密码工具
|   |   |   |-- user_admin_service.py # 用户管理服务
|   |   |   |-- user_context.py       # 用户上下文（目录隔离）
|   |   |   |-- metrics_service.py    # 指标采集
|   |   |   |-- file_preview_service.py  # 文件预览
|   |   |   |-- dataset_export_service.py  # 数据集导出
|   |   |   |-- qa_document_ingest_service.py  # 文档入库
|   |   |   |-- qa_document_parser.py  # 文档解析
|   |   |   |-- qa_knowledge_service.py  # 知识库服务
|   |   |   |-- qa_model_diagnostic_service.py  # 模型诊断
|   |   |   |-- qa_text_splitter.py   # 文本分块
|   |   |   |-- qa_chat_service.py    # QA 聊天服务
|   |   |   |-- skill_template_service.py  # 技能模板
|   |   |   |-- mock_agent_scenarios.py  # Mock 场景
|   |   |   |-- mock_ai.py            # Mock AI
|   |   |   |-- agent_blueprint_store.py  # 蓝图存储（538 LOC，v1.7 新增）
|   |   |   |-- agent_blueprint_service.py  # 蓝图业务逻辑（374 LOC，v1.7 新增）
|   |   |   |-- agent_blueprint_validator.py  # 蓝图校验（129 LOC，v1.7 新增）
|   |   |   |-- agent_blueprint_diff_service.py  # 蓝图版本对比（107 LOC，v1.7 新增）
|   |   |   |-- agent_blueprint_import_export.py  # 蓝图导入导出（107 LOC，v1.7 新增）
|   |   |   |-- agent_blueprint_preview_service.py  # 蓝图预览（48 LOC，v1.7 新增）
|   |   |   |-- agent_blueprint_release_gate.py  # 蓝图发布门禁（106 LOC，v1.7 新增）
|   |   |   |-- agent_blueprint_seed_service.py  # 蓝图种子数据（93 LOC，v1.7 新增）
|   |   |
|   |   |-- schemas/     (3 个文件)    # Pydantic 请求/响应模型
|   |   |   |-- agent_runs.py
|   |   |   |-- chat.py
|   |   |   |-- conversations.py
|   |   |
|   |   |-- workflows/   (7 个文件 + 6 步骤)  # 工作流编排
|   |   |   |-- video_script_workflow.py         # 视频脚本拆解（已生产化，214 LOC）
|   |   |   |-- competitor_analysis_workflow.py  # 竞品分析
|   |   |   |-- detail_page_planning_workflow.py # 详情页策划
|   |   |   |-- focused_agent_workflow.py        # 聚焦智能体（160 LOC）
|   |   |   |-- generic_agent_workflow.py        # 通用智能体
|   |   |   |-- main_image_breakdown_workflow.py # 主图拆解
|   |   |   |-- smart_selection_workflow.py      # 智能选款
|   |   |   |-- steps/                           # 可复用步骤
|   |   |       |-- video_frame_step.py          # 视频帧提取
|   |   |       |-- subtitle_ocr_step.py         # 字幕 OCR
|   |   |       |-- subtitle_align_step.py       # 字幕对齐
|   |   |       |-- quality_check_step.py        # 质量检查
|   |   |       |-- excel_export_step.py         # Excel 导出
|   |   |
|   |   |-- tests/      (16 个文件)   # 单元测试
|   |   |   |-- test_agent_blueprint_api.py          # 蓝图 API 测试（100 LOC）
|   |   |   |-- test_agent_blueprint_diff.py         # 蓝图对比测试（36 LOC）
|   |   |   |-- test_agent_blueprint_import_export.py # 蓝图导入导出测试（52 LOC）
|   |   |   |-- test_agent_blueprint_preview.py      # 蓝图预览测试（20 LOC）
|   |   |   |-- test_agent_blueprint_publish_flow.py # 蓝图发布流程测试（44 LOC）
|   |   |   |-- test_agent_blueprint_release_gate.py # 蓝图发布门禁测试（45 LOC）
|   |   |   |-- test_agent_blueprint_service.py      # 蓝图服务测试（81 LOC）
|   |   |   |-- test_agent_blueprint_store.py        # 蓝图存储测试（46 LOC）
|   |   |   |-- test_agent_blueprint_test_runs.py    # 蓝图测试运行测试（36 LOC）
|   |   |   |-- test_agent_blueprint_validation_history.py  # 蓝图验证历史测试（34 LOC）
|   |   |   |-- test_agent_blueprint_validator.py    # 蓝图校验器测试（65 LOC）
|   |   |   |-- test_agent_runs_api.py               # Agent Run API 测试
|   |   |   |-- test_auth_service.py                 # 认证服务测试
|   |   |   |-- test_conversation_store.py           # 会话存储测试
|   |   |   |-- test_task_store.py                   # 任务存储测试
|   |   |   |-- test_video_result_normalizer.py      # 视频结果规范化测试
|   |   |
|   |   |-- scripts/
|   |   |   |-- smoke_minimal.py     # 最小 smoke 测试脚本
|   |   |
|   |   |-- models/                   # 本地 BGE 模型（gitignore）
|   |   |-- runtime/                  # 运行时数据（gitignore）
|   |   |-- uploads/                  # 上传文件（gitignore）
|   |
|   |-- web/                          # Next.js 14 前端
|       |-- src/
|           |-- app/       (8 pages + 1 layout)   # App Router 页面
|           |   |-- page.tsx              # 首页
|           |   |-- login/page.tsx        # 登录
|           |   |-- agent/page.tsx        # AI 智能体（核心工作台）
|           |   |-- agents/page.tsx       # 智能体列表
|           |   |-- chat/page.tsx         # AI 对话
|           |   |-- ai-creation/page.tsx  # AI 创作
|           |   |-- board/page.tsx        # 无限画板
|           |   |-- competition-diagnosis/page.tsx  # 竞品分析
|           |
|           |-- components/ (31 个文件 + 7 ui)    # UI 组件
|           |   |-- AgentBlueprintEditor.tsx     # 蓝图结构化编辑器（v1.7 新增，187 LOC）
|           |   |-- AgentBlueprintPanel.tsx      # 蓝图中心面板（v1.7 新增，274 LOC）
|           |   |-- AgentWorkspace.tsx / AgentCard.tsx / AgentRunStatus.tsx
|           |   |-- GenericAgentPanel.tsx / VideoScriptAgentPanel.tsx (391 LOC)
|           |   |-- VideoBreakdownResultPanel.tsx
|           |   |-- ConversationPanel.tsx / ConversationMessages.tsx
|           |   |-- KnowledgeBasePanel.tsx / DatasetPanel.tsx
|           |   |-- AdminConsolePanel.tsx / UserManagementPanel.tsx
|           |   |-- DebugPayloadPanel.tsx / PayloadPreviewModal.tsx
|           |   |-- RuntimeHealthPanel.tsx / Sidebar.tsx / AppShell.tsx
|           |   |-- AuthGuard.tsx / FilePreviewPanel.tsx / DataCleaningPanel.tsx
|           |   |-- FieldMappingPanel.tsx / AgentConfigPanel.tsx / AgentConnectorPanel.tsx
|           |   |-- DatasetSelector.tsx / SkillSelectorPanel.tsx
|           |   |-- AgentSelectorPopover.tsx / ChatInput.tsx / QuickPrompts.tsx
|           |   |-- MockAnswer.tsx
|           |   |-- ui/                  # 通用 UI 原子组件
|           |       |-- ConfirmDialog / EmptyState / ErrorState
|           |       |-- LoadingState / SafeDrawer / SafeScrollableModal / StatusBadge
|           |
|           |-- lib/       (8 个文件)      # 工具层
|           |   |-- api.ts       (1,217 LOC)  # 统一 API client（fetch + JWT + 错误处理）
|           |   |-- auth.ts               # 认证状态管理
|           |   |-- agents.ts             # Agent 定义/注册（81 LOC）
|           |   |-- perf.ts               # 开发环境性能探针
|           |   |-- navigation.ts         # 导航配置
|           |   |-- safeFallbacks.ts      # 安全降级
|           |   |-- mockData.ts           # Mock 数据
|           |   |-- queryKeys.ts          # SWR 查询 key 管理
|           |
|           |-- hooks/     (16 个文件)
|           |   |-- useAgentBlueprints.ts  # SWR 封装蓝图列表/详情/版本/测试（v1.7 新增）
|           |   |-- useAgentConfigs.ts     # SWR 封装 Agent 配置（v1.7 新增）
|           |   |-- useAgentConnectors.ts  # SWR 封装 Connector（v1.7 新增）
|           |   |-- useAgentRunEvents.ts   # SSE 事件驱动 run 状态（v1.7 新增，84 LOC）
|           |   |-- useAgentConversations.ts  # SWR 封装 agent 会话列表
|           |   |-- useQAConversations.ts     # SWR 封装 QA 会话列表
|           |   |-- useKnowledgeStats.ts      # SWR 封装知识库统计
|           |   |-- useRuntimeHealth.ts       # SWR 封装运行时健康
|           |   |-- useStorageHealth.ts       # SWR 封装存储健康
|           |   |-- useCurrentUser.ts         # SWR 封装当前用户
|           |   |-- useAgentRunPolling.ts     # Agent Run 轮询（SSE 失败 fallback）
|           |   |-- useAdminUsers.ts          # SWR 封装管理员列表（v1.7 新增）
|           |   |-- useDatasets.ts            # SWR 封装数据集列表（v1.7 新增）
|           |   |-- useDebugPayloads.ts       # SWR 封装 Debug Payload（v1.7 新增）
|           |   |-- useFiles.ts               # SWR 封装文件列表（v1.7 新增）
|           |   |-- useSkills.ts              # SWR 封装技能模板（v1.7 新增）
|           |
|           |-- globals.css               # Tailwind 全局样式
|
|-- docs/                             # 产品与技术文档 (17 个文件 + 1 archive/)
|   |-- PRD.md                        # 产品需求文档
|   |-- API.md                        # API 文档
|   |-- API_fixed.md                  # API 文档修复记录（v1.7 新增）
|   |-- AGENT_BLUEPRINTS.md           # 蓝图中心设计文档（v1.7 新增，125 LOC）
|   |-- FRONTEND_DATA_LAYER.md        # 前端数据层规范（v1.7 新增，34 LOC）
|   |-- TESTING.md                    # 测试规范文档（v1.7 新增，49 LOC）
|   |-- CODEX_HANDOFF.md              # 接手交接说明
|   |-- NEXT_TASKS.md                 # 下一步任务
|   |-- CHANGELOG_CONTEXT.md          # 跨窗口变更记录
|   |-- STORAGE_SQLITE.md             # 存储架构说明
|   |-- AGENT_PERFORMANCE_NOTES.md    # 性能优化笔记
|   |-- TODO.md                       # 已完成清单
|   |-- SMOKE_TESTS.md                # 烟雾测试说明
|   |-- VIDEO_AGENT_SETUP.md          # 视频 Agent 配置
|   |-- VIDEO_AGENT_E2E_CHECKLIST.md  # 视频 Agent E2E 检查清单
|   |-- RAG_MODEL_SETUP.md            # RAG 模型配置
|   |-- PRD_fixed.md                  # PRD 修复记录（v1.7 新增）
|   |-- archive/                      # 归档文档
|       |-- legacy_bak_v1.5.7/        # 历史备份
|
|-- AGENTS.md                         # AI Agent 协作规则
|-- ARCHITECTURE_REVIEW.md            # v1.5.7 架构评审
|-- ARCHITECTURE_EVALUATION_REPORT.md # 本文件（v1.7.1 架构评估）
|-- start-dev.ps1 / .bat              # 一键启动脚本
|-- docker-compose.yml                # Docker Compose 配置
|-- docker-compose.prod.yml           # Docker Compose 生产配置
|-- Dockerfile.api                    # API 容器镜像
|-- Dockerfile.web                    # Web 容器镜像
|-- .github/workflows/ci.yml          # GitHub Actions CI
|-- .env / .env.example
|-- .gitignore
|-- README.md
```

---

## 四、架构分析

### 4.1 整体架构图

```
+----------------------------------------------------------+
|                    浏览器 (Next.js 14 SPA)                |
|  +---------+ +----------+ +----------+ +-------------+  |
|  | /agent  | |  /chat   | | /board   | | /ai-creation|  |
|  +----+----+ +----+-----+ +----+-----+ +------+------+  |
|       +-----------+------------+-------------+          |
|                         | api.ts (统一 fetch + JWT)       |
|                    +----+----+                             |
|                    |   SWR   | (缓存/去重/重验证)          |
|              16 hooks (读取型数据层，v1.7 大幅扩展)        |
|                    +----+----+                             |
|              +-----+-----+-----+                          |
|              |           |         |                       |
|          SSE Events   Polling   mutate                     |
|          (run 状态)  (fallback) (写后刷新)                  |
|              +-----+-----+-----+                          |
+-------------------------+--------------------------------+
                          | HTTP / SSE
+-------------------------+--------------------------------+
|  FastAPI 后端           |                                  |
|  +----------------------+-----------------------------+   |
|  |  routers/ (16个)  ← 参数校验 + 鉴权 + 调用 service  |   |
|  +----------------------------------------------------+   |
|  |  services/ (63个) ← 业务逻辑，不感知 HTTP           |   |
|  |  +-- storage (app_sqlite, task, conversation, qa)   |   |
|  |  +-- ai (deepseek_client, qa_rag_*)                 |   |
|  |  +-- video (video_agent_*, normalizer, workflows)   |   |
|  |  +-- blueprint (8 services, v1.7 新增)              |   |
|  |  +-- security (auth, token, audit, security_config) |   |
|  +----------------------------------------------------+   |
|  |  workflows/ (7+6) ← 编排层，组合 service            |   |
|  +----------------------------------------------------+   |
|  |  schemas/ (3)     ← Pydantic 请求/响应              |   |
|  +----------------------------------------------------+   |
|           |                         |                      |
|     +-----+------+           +------+------+              |
|     | APP SQLite |           | RAG SQLite  |              |
|     | (OLTP)     |           | (向量检索)  |              |
|     +------------+           +-------------+              |
|           |                                                |
|     +-----+----------------------------------+            |
|     | External: DeepSeek API / Local Agent    |            |
|     | (http://localhost:8001)                 |            |
|     +-----------------------------------------+            |
+----------------------------------------------------------+
```

### 4.2 后端分层架构

后端采用经典的四层分离：

```
routers/   →  HTTP 层：参数校验、鉴权、调用 service（薄）
services/  →  业务逻辑：纯 Python，不碰 FastAPI 对象
schemas/   →  Pydantic：请求/响应结构统一
workflows/ →  编排层：组合多个 service 完成复杂任务
```

**评价**：这是 FastAPI 社区的推荐模式，职责边界清晰。63 个 service 文件分工明确，最大单文件约 538 LOC（`agent_blueprint_store.py`），`conversation_store.py` 406 LOC。蓝图中心的 8 个 service 进一步细分了存储、校验、对比、导入导出、预览、发布门禁等职责。

### 4.3 双 SQLite 存储架构（核心设计）

```
+------------------------------+  +------------------------------+
|        APP SQLite            |  |        RAG SQLite            |
|  runtime/app/                |  |  runtime/rag/                |
|  meizhaiseek.sqlite3         |  |  rag.sqlite3                 |
|                              |  |                              |
|  * users (用户/权限)         |  |  * documents (知识库文档)    |
|  * audit_logs (审计)         |  |  * chunks (文本块)           |
|  * agent_runs (任务)         |  |  * embeddings (向量)         |
|  * agent_conversations       |  |                              |
|  * agent_messages            |  |  只存知识库向量              |
|  * qa_conversations          |  |  不存账号/任务               |
|  * qa_messages               |  |                              |
|  * datasets (元数据)         |  |                              |
|  * dataset_files             |  |                              |
|  * dataset_jobs              |  |                              |
|  * files / artifacts         |  |                              |
|  * debug_payloads            |  |                              |
|  * local_agent_connectors    |  |                              |
|  * app_kv / schema_migrations|  |                              |
|  * agent_blueprints          |  |  (v1.7 新增)                 |
|  * agent_blueprint_versions  |  |                              |
|  * agent_blueprint_test_cases|  |                              |
|  * agent_blueprint_releases  |  |                              |
|  * agent_blueprint_test_runs |  |                              |
|  * agent_blueprint_validation|  |  (v1.7 新增)                 |
|                              |  |                              |
|  21 张表 + 27 个索引         |  |  3 张表                      |
|  只存平台运行数据，           |  |                              |
|  不存 embedding              |  |                              |
+------------------------------+  +------------------------------+
```

**切分理由**：APP SQLite 以 OLTP 增删改查为主（事务一致性），RAG SQLite 以向量相似度检索为主（数据量大但读写不频繁）。合在一起会导致向量膨胀拖慢事务、事务锁阻塞检索。

**v1.7 新增 6 张蓝图表** 全部存入 APP SQLite，因为它们描述的是方法论配置元数据（状态、版本、测试用例、发布记录、验证结果），属于 OLTP 读写模式，与 agent_runs / agent_conversations 关联紧密。

### 4.4 安全模型

| 安全机制 | 实现方式 | 状态 |
|----------|----------|------|
| 用户隔离 | 所有数据路径按 `user_id` 分区 | 已实现 |
| 角色权限 | admin > operator > viewer（viewer 只读） | 已实现 |
| 密码安全 | PBKDF2 哈希 + auth_version 递增 | 已实现 |
| Token | HMAC JWT，环境变量配置 secret 和过期时间 | 已实现 |
| 凭证脱敏 | 审计日志/Debug Payload 全程 `_redact()` | 已实现 |
| 下载安全 | 安全目录校验 + 文件所有权校验 | 已实现 |
| Secret 生成 | 未配置时自动生成 `generated_secrets.json` | 已实现 |
| 安全警告 | runtime health 输出安全 warnings | 已实现 |
| 密码策略 | 检测默认密码并警告 | 已实现 |
| 蓝图权限 | admin 发布/回滚/停用；operator 编辑/测试；viewer 只读已发布 | **v1.7 新增** |
| 蓝图脱敏 | 导入导出递归移除 password/token/api_key/secret | **v1.7 新增** |
| 蓝图校验 | Validator 校验变量引用、renderer 白名单、Connector 存在性 | **v1.7 新增** |

### 4.5 API 设计

- **16 个路由模块**（v1.6.4 为 15，新增 `agent_blueprints`），统一 `/api` 前缀
- RESTful 风格，前后端分离
- SSE 流式输出（AI 问答 `/api/qa/chat/stream` + Agent Run 事件 `/api/agent-runs/{run_id}/events`）
- 前端统一走 `api.ts`（1,217 LOC）封装的 fetch，自动注入 JWT，401 自动跳转登录
- 关键性能优化：`/api/agent-runs/{run_id}/summary`（轻量轮询）、`/api/agent-runs/{run_id}/result`（按需加载完整结果）
- Payload Preview `/api/agent-runs/preview-payload`（调试用）
- **蓝图 API**（v1.7）：30+ 端点覆盖 CRUD、版本管理、diff、validate、release-gate、publish、rollback、clone、enable/disable/deprecate、test-case CRUD、test-run、preview/input、preview/list、import、export、releases

### 4.6 前端架构

- **App Router** 模式，8 个页面 + 1 个根 layout
- **31 个 UI 组件 + 7 个 ui 原子组件**，覆盖 Agent、QA、Dataset、蓝图中心、后台管理
- **8 个 lib 工具**：api client、auth、agent registry、perf 探针、queryKeys
- **16 个 hooks**（v1.6.4 为 7，+9 新增）：涵盖 SSE 事件、SWR 数据层、轮询 fallback
- 前端 API 层 1,217 LOC，类型定义完整（80+ TypeScript type/interface）
- **SWR 数据层**（v1.6.4 引入，v1.7 大幅扩展）：
  - 读取型：`useAgentBlueprints`、`useAgentConfigs`、`useAgentConnectors`、`useAgentConversations`、`useQAConversations`、`useKnowledgeStats`、`useRuntimeHealth`、`useStorageHealth`、`useCurrentUser`、`useAdminUsers`、`useDatasets`、`useDebugPayloads`、`useFiles`、`useSkills`
  - 运行态：`useAgentRunEvents`（SSE 优先）、`useAgentRunPolling`（fallback）
- 数据层规范文档：`docs/FRONTEND_DATA_LAYER.md`（v1.7 新增，明确 SWR/mutate/边界）

### 4.7 智能体蓝图中心（v1.7 核心新增）

蓝图中心是 v1.7 最重要的架构扩展，为平台引入**方法论配置与治理能力**。

#### 4.7.1 架构定位

```
Agent Registry (运行时)  ←──  Blueprint (方法论描述)
       ↓                           ↓
   真正执行任务的智能体        描述智能体的"做什么、怎么做、怎么验"
       ↓                           ↓
   workflows/                  input_schema → methodology → execution_config → output_schema
```

**设计原则**：
- Blueprint **只描述现有能力**，不重写运行链路
- Agent Registry 始终是运行时智能体注册来源，没有蓝图的智能体不会消失
- Blueprint 为 Registry 补充方法论、版本、输入输出、测试和发布信息
- 蓝图的 methodology steps 用于描述、校验和验收，**不会动态执行任意 JSON/Python**

#### 4.7.2 生命周期与权限

| 状态 | 说明 | 权限 |
|------|------|------|
| `draft` | 草稿，可编辑/复制/删除 | operator+ |
| `testing` | 测试中，可运行测试用例 | operator+ |
| `published` | 已发布，正式展示 | admin 发布 |
| `disabled` | 已停用，拒绝新任务 | admin 操作 |
| `deprecated` | 已废弃，只读保留 | admin 操作 |

已发布版本不直接覆盖。修改已发布蓝图必须创建新版本；回滚会复制目标历史发布版本为新版本。

#### 4.7.3 核心数据结构

```
agent_blueprints (主表：blueprint_id, agent_id, name, status, current_version_id, published_version_id)
    ↓ 1:N
agent_blueprint_versions (版本：input_schema, methodology, prompt_config, execution_config, output_schema, result_ui_config, acceptance_rules)
    ↓ 1:N
agent_blueprint_test_cases (测试用例：input, expected_status, expected_result_rules, expected_artifacts)
    ↓ 1:N
agent_blueprint_test_runs (测试运行记录：agent_run_id, status, result_summary, validation_result)
    ↓ 1:N
agent_blueprint_validation_results (校验结果：errors, warnings, validator_version)
    ↓ 1:N
agent_blueprint_releases (发布记录：publish/rollback/disable/enable/deprecate)
```

#### 4.7.4 服务层设计

| 服务 | 职责 | LOC |
|------|------|-----|
| `agent_blueprint_store.py` | 蓝图/版本/测试用例/发布/校验的 CRUD | 538 |
| `agent_blueprint_service.py` | 业务编排：创建/编辑/版本/校验/发布/回滚/复制/种子 | 374 |
| `agent_blueprint_validator.py` | 结构校验、变量引用、renderer 白名单、Connector 存在性、Prompt 脱敏 | 129 |
| `agent_blueprint_diff_service.py` | 版本对比（新增/修改/删除字段识别） | 107 |
| `agent_blueprint_import_export.py` | 导入（含 preview）/ 导出（含递归脱敏） | 107 |
| `agent_blueprint_preview_service.py` | 输入表单预览 / 输出结果预览 | 48 |
| `agent_blueprint_release_gate.py` | 发布前置校验：完整性、校验通过、测试通过 | 106 |
| `agent_blueprint_seed_service.py` | 首次启动自动播种视频拆解蓝图 | 93 |

#### 4.7.5 前端蓝图组件

- **AgentBlueprintPanel.tsx**（274 LOC）— 蓝图中心主面板：列表、详情、版本管理、发布操作
- **AgentBlueprintEditor.tsx**（187 LOC）— 结构化编辑器：input types（14 种）、failure policies、execution types、renderers（5 种白名单）、output types（14 种）
- **useAgentBlueprints.ts** — SWR hooks（蓝图列表、详情、diff、测试运行、校验历史）

### 4.8 异步 I/O 层

- `deepseek_client.py` — `async_generate_answer()` 和 `async_stream_answer()` 包装
- **`async_store_utils.py`**（v1.7 新增）— 将同步 SQLite 操作（task_store、conversation_store、audit_log_service）包装为 async，使用 `asyncio.to_thread`
- **`legacy_json_fallback.py`**（v1.7 新增）— 集中式旧 JSON fallback 开关控制，默认关闭

### 4.9 SSE 事件驱动（v1.7 新增能力）

- 新增 `useAgentRunEvents` hook（84 LOC），通过 SSE `/api/agent-runs/{run_id}/events` 实时接收 run 状态变更
- 状态机：`idle → connecting → connected → fallback`（SSE 失败自动降级到 polling）
- 配合原有的 `useAgentRunPolling` 形成双通道冗余
- SWR 不参与 run 状态高频刷新（遵循 `FRONTEND_DATA_LAYER.md` 规范）

### 4.10 CI/CD 与容器化

| 能力 | 实现 | 状态 |
|------|------|------|
| Docker 镜像 | `Dockerfile.api` + `Dockerfile.web` | 已补全 |
| Docker Compose | `docker-compose.yml` 双服务 + `docker-compose.prod.yml` 生产配置 | 已补全 |
| GitHub Actions | `ci.yml` — compileall + unittest + pytest + npm build | 已补全（v1.7 增加 pytest） |
| Smoke 测试 | `smoke_minimal.py` + `docs/SMOKE_TESTS.md` | 已补全 |
| 单元测试 | 16 个测试文件覆盖蓝图/service/store | **v1.7 大幅扩展** |
| 测试规范 | `docs/TESTING.md` — 本地/视频 E2E/单元测试/pytest | **v1.7 新增** |

---

## 五、版本演进路线

| 版本 | 核心能力 |
|------|----------|
| v0.1–v0.4 | 基础页面、视频展示、主导航、智能体选择 |
| v0.5–v0.9 | 多 Agent 任务中心、配置中心、技能模板 |
| v1.0 | 配置治理、健康检查、Debug Payload |
| v1.1 | 前端登录、文案整理 |
| v1.2 | **鉴权 + 用户隔离 + 审计** |
| v1.3 | Connector 管理、Payload Preview |
| v1.4 | 管理员控制台 |
| v1.5 | Dataset 清洗中心 |
| v1.5.1 | 会话持久化修复 |
| v1.5.2 | RAG 问答（DeepSeek + BGE） |
| v1.5.3 | 知识库入库与管理 |
| v1.5.4 | 会话栏交互优化 |
| v1.5.5 | 模型状态与 RAG 诊断 |
| v1.5.6 | DeepSeek 流式输出（SSE） |
| **v1.5.7** | **APP SQLite 迁移**（关键架构升级） |
| v1.5.8 | 增量 upsert、Dataset SQLite、service_events |
| v1.6 | 视频拆解生产化 |
| v1.6.1 | 会话切换卡死修复 |
| v1.6.2 | 性能深度优化（轻量 payload、单一轮询、延迟加载） |
| v1.6.4 | 架构评估 P1-P3 工程规范补全（SWR、async、CI、Docker、smoke、security） |
| **v1.7** | **智能体蓝图中心**（6 张新表 + 8 services + 1 router + 30+ API + 编辑器 + 测试） |
| **v1.7.1** | **蓝图发布闭环**（release-gate、publish、rollback、diff、validation history、test runs、seed） |

从 v0.1 到 v1.7.1，项目经历了约 **20 个版本迭代**，功能增长显著，架构持续演进。

---

## 六、设计亮点

### 6.1 双 SQLite 边界划分合理
APP/RAG 分离的架构决策体现了对数据读写模式的深入理解。切分理由充分，不是过度设计。21 张表分工明确，27 个索引覆盖查询路径。

### 6.2 迁移工程扎实
```
备份 → 幂等写入 → 报告 → 兼容读取（SQLite fallback JSON）
```
- 不删除源文件
- `INSERT OR IGNORE` + `ON CONFLICT DO UPDATE`
- 每个服务先查 SQLite，找不到再 fallback 读 JSON 并自动写回
- v1.7 将 fallback 开关集中到 `legacy_json_fallback.py`，默认关闭

### 6.3 可运维性设计完善
- Config 的 backup / repair / reset 三条路径
- Zombie 任务自动回收（`agent_run_maintenance`）
- 运行健康检查返回 warnings 列表
- 审计日志支持筛选 + CSV/JSONL 双格式导出
- Debug Payload 支持 request/response 查看和 replay 重放
- RAG 诊断链路完整
- 安全配置服务：自动生成 secret、密码策略检测、安全 warnings

### 6.4 安全意识有底线
- 用户隔离不是"检查一下"，而是存储路径本身就按用户分
- 审计日志全程脱敏
- 文件下载双重校验
- local agent 不可达时真实 failed，不伪造成功
- 前端不允许直连 local agent
- 运行时安全警告：默认 secret / 默认密码实时检测
- **蓝图脱敏**（v1.7）：导入导出自动移除敏感字段，Prompt 禁止保存 password/token/api_key

### 6.5 蓝图中心设计务实（v1.7）
- **只描述不执行**：避免任意代码/shell 注入风险
- **分层校验**：Validator（结构）→ Release Gate（发布条件）→ 运行时（真正执行）
- **版本不可变**：已发布版本不覆盖，修改必须创建新版本
- **权限分明**：admin/operator/viewer 三级管控
- **测试驱动**：test_case → test_run（复用真实 Agent Run API）→ PASS/FAIL 回写
- **白名单机制**：renderer 仅允许 5 种注册值，input_type 仅 14 种

### 6.6 性能优化到位
- 会话切换 AbortController + requestSeq 防竞态
- SSE 事件驱动 + polling fallback 双通道
- 统一 `useAgentRunPolling` hook，消除重复 setInterval
- 后端 payload 轻量化（summary/result 分离）
- 大 JSON 延迟加载 + 分段渲染

### 6.7 数据层规范化（v1.7 扩展）
- 16 个 hooks 覆盖全部读取场景（v1.6.4 仅 6 个）
- queryKeys 统一管理缓存 key
- 请求去重、自动重试、聚焦时重验证
- `FRONTEND_DATA_LAYER.md` 明确 SWR/mutate/边界规范
- SSE 事件与 SWR 职责分工明确（运行态 vs 读取型）

### 6.8 工程规范补全（v1.7 扩展）
- GitHub Actions CI 增加 pytest 环节
- 16 个单元测试文件（v1.6.4 为 0 正式测试文件）
- 559 LOC 蓝图测试覆盖全链路
- 视频 Agent E2E 自动化（smoke + require flag）
- 文档归档 + 数据层规范 + 测试规范

---

## 七、已知问题与风险

### 7.1 已修复（v1.6.4→v1.7.1 期间）

| 原问题 | 修复版本 | 修复方式 |
|--------|----------|----------|
| 无正式单元测试 | v1.7 | 新增 16 个测试文件覆盖 core/blueprint/video |
| 蓝图中心缺失 | v1.7 | 新增 8 services + 1 router + 30+ API + 6 张表 |
| 蓝图发布流程缺失 | v1.7.1 | 新增 release-gate/publish/rollback/diff/validation/test-runs |
| SSE 事件驱动缺失 | v1.7 | 新增 `useAgentRunEvents` hook |
| 前端 SWR 覆盖不足 | v1.7 | hooks 从 6 扩充到 16，覆盖所有读取场景 |
| 蓝图配置无版本治理 | v1.7 | 完整版本模型（version → release → rollback → clone） |
| 旧 JSON fallback 分散 | v1.7 | 集中到 `legacy_json_fallback.py`，默认关闭 |
| 测试规范缺失 | v1.7 | 新增 `docs/TESTING.md` + `docs/FRONTEND_DATA_LAYER.md` |
| async 包装不足 | v1.7 | 新增 `async_store_utils.py` 统一包装 store 操作 |

### 7.2 项目运维层面

| 问题 | 说明 | 建议 |
|------|------|------|
| 测试覆盖仍需提升 | 蓝图 11 个测试文件但缺少集成/E2E | 增加端到端测试覆盖完整发布流程 |
| `docker-compose` 使用 dev 模式 | `Dockerfile.web` 用 `npm run dev` | 生产部署时调整为 build+start |
| 旧 JSON fallback 仍存在 | `legacy_json_fallback.py` 保留读取路径 | 确认迁移完成后移除 fallback |
| `agent_blueprint_store.py` 体积较大 | 538 LOC 承担过多 CRUD 职责 | 可考虑拆分 version/release/test-case 存储 |

### 7.3 架构层面（低优先级）

| 问题 | 影响 | 优先级 |
|------|------|--------|
| Blueprint Editor 仅结构化编辑 | 复杂 methodology 配置可能不够直观 | P3（后续可考虑可视化编排） |
| 蓝图与 Registry 同步是种子方式 | 首次启动自动播种 video 蓝图，后续手动维护 | P3 |
| 异步 I/O 仅覆盖部分 store | SQLite 操作主路径仍是同步 | P3 |
| 无 WebSocket 广播 | 多用户场景下状态同步依赖轮询/SSE | P3 |
| `api.ts` 体积偏大 | 1,217 LOC 包含全部 API 定义 | P3（可考虑按模块拆分） |
| Blueprint Validator 仅静态校验 | 不验证执行链路的实际可达性 | P3 |

---

## 八、综合评分

| 评估维度 | 评分 | 说明 | 变化 |
|----------|------|------|------|
| **架构合理性** | ★★★★★ | 双 SQLite + 分层 + 蓝图中心架构完整 | ↑ |
| **代码质量** | ★★★★☆ | 写法一致，蓝图中心模块化解耦好 | ↑ |
| **安全性** | ★★★★★ | 用户隔离、凭证脱敏、蓝白板名单/脱敏/权限 | ↑ |
| **可维护性** | ★★★★★ | 文档 17 个 + 数据层规范 + 测试规范，接手友好 | ↑ |
| **可运维性** | ★★★★★ | backup/repair/reset/health/migration/debug/security/blueprint | — |
| **扩展性** | ★★★☆☆ | 单机 SQLite 但蓝图中心提供方法论层扩展性 | ↑ |
| **前端架构** | ★★★★★ | 16 hooks 全 SWR 覆盖 + SSE 双通道 + 数据层规范 | ↑↑ |
| **测试覆盖** | ★★★☆☆ | 16 个文件 + 559 LOC 蓝图测试，但仍缺 E2E | ↑↑ |
| **文档质量** | ★★★★★ | PRD/API/STORAGE/HANDOFF/TESTING/DATA_LAYER/BLUEPRINTS 齐全 | ↑ |
| **工程规范** | ★★★★★ | AGENTS.md + CI + Docker + pytest + unittest 完整 | ↑ |
| **持久化可靠性** | ★★★★★ | 双 SQLite 21 表 + 27 索引，迁移工程扎实，蓝版图完整 | ↑ |

**总评：★★★★★ (4.5/5)** — v1.7.1 在 v1.6.4 工程补全的基础上，新增智能体蓝图中心这一重量级模块，从"能用"进化到"可治理"。蓝图中心的设计体现了对 AI Agent 方法论配置、版本管理、发布流程的深度思考，6 张蓝图表 + 8 个 service 的实现务实且安全。

---

## 九、后续优化建议

| 优先级 | 事项 | 预期收益 |
|--------|------|----------|
| 🟠 P1 | 增加蓝图发布端到端测试（draft → test → validate → publish → rollback） | 保障核心发布链路 |
| 🟠 P1 | 扩大测试覆盖到 conversation_store、task_store、auth_service 现有测试之外的核心路径 | 防止回归 |
| 🟡 P2 | 拆分 `agent_blueprint_store.py`（538 LOC）为 version/release/test-case 独立存储 | 降低单文件复杂度 |
| 🟡 P2 | 确认 JSON 迁移完成后移除 legacy fallback 代码 | 简化代码路径 |
| 🟡 P2 | Docker Compose 生产模式配置（build+start 替代 npm run dev） | 标准化部署 |
| 🟡 P2 | 增加集成测试覆盖 SSE 事件驱动链路 | 保障实时状态同步可靠性 |
| 🟢 P3 | SQLite 操作逐步 async 化（`aiosqlite` 或扩展 `async_store_utils`） | 提升并发吞吐 |
| 🟢 P3 | 蓝图 Editor 可视化编排（drag-and-drop methodology steps） | 降低配置门槛 |
| 🟢 P3 | `api.ts` 按模块拆分（agent/blueprint/qa/dataset/admin） | 降低维护负担 |
| 🟢 P3 | WebSocket 广播替代高频轮询（多用户状态同步场景） | 降低延迟 |
| 🟢 P3 | 蓝图 Registry 自动同步（不再是种子式，而是双向绑定） | 减少手动维护 |

---

## 十、总结

meizhaiseek-platform 是一个**快速迭代、功能丰富、架构务实且持续进化**的 AI 平台项目。从 v0.1 到 v1.7.1 的演进路径清晰，每个版本都有明确的核心交付。

**六大架构亮点**：
1. **双 SQLite 存储设计** — APP/RAG 边界划分合理，21 表 + 27 索引覆盖全业务
2. **JSON → SQLite 的安全迁移** — 备份、幂等、兼容读取，迁移工程扎实
3. **完善的可运维性工具链** — backup/repair/reset/health/migration/debug/security/blueprint
4. **SWR + SSE 双通道数据层**（v1.7）— 16 个 hooks 覆盖读取场景，SSE 事件驱动运行态
5. **智能体蓝图中心**（v1.7）— 方法论配置、版本治理、发布门禁、测试运行一体化
6. **工程规范全面**（v1.7.1）— CI + Docker + unittest + pytest + smoke + 测试/数据层规范文档

**v1.7 → v1.7.1 版本关键进展**：
- 新增智能体蓝图中心：6 张表 + 8 services + 1 router + 30+ API 端点
- 新增蓝图发布闭环：release-gate → publish / rollback / disable / deprecate
- 新增蓝图版本对比（diff）与校验历史（validation history）
- 新增蓝图测试运行（test cases → test runs → PASS/FAIL 回写）
- 新增蓝图导入导出（with preview + 递归脱敏）
- 新增 `AgentBlueprintEditor` 结构化编辑器（14 input types + 14 output types + 5 renderers）
- 新增 `useAgentRunEvents` SSE 事件驱动 hook + polling fallback 双通道
- 前端 SWR hooks 从 6 扩充到 16，覆盖所有读取场景
- 新增 `async_store_utils` 统一异步包装 + `legacy_json_fallback` 集中开关
- 新增 16 个单元测试文件（559 LOC 蓝图测试 + core/video 测试）
- 新增 `docs/TESTING.md` + `docs/FRONTEND_DATA_LAYER.md` + `docs/AGENT_BLUEPRINTS.md`
- CI 增加 pytest 环节，形成 compileall + unittest + pytest + build 完整流水线

**一句话评价**：8 个 Python 生产依赖（+1 test）、0 个外部数据库、一个脚本就能跑起来——v1.7.1 在保持"简洁"基因的同时，通过蓝图中心为 AI Agent 引入了企业级的治理与版本能力，架构成熟度从"功能完整"迈向"可治理、可审计、可演进"。