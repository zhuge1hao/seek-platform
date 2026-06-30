# meizhaiseek-platform PRD

## v1.6.2：AI 智能体页面卡顿深度优化

v1.6.2 针对 `/agent?conversation_id=` 会话切换时仍存在卡顿的问题进行深度优化。该版本从请求、轮询、状态更新、后端 payload、前端渲染多个层面处理性能瓶颈：会话切换只加载轻量摘要，重结果、Debug Payload、artifact 详情延迟加载；统一 agent run 轮询，避免多个组件重复轮询；结果面板按 Tab 和“加载更多”分段渲染；大 JSON 默认折叠截断；会话列表减少重复刷新，从而避免 React 主线程被大 payload 阻塞。

## v1.6.1：AI 智能体会话切换稳定性修复

v1.6.1 修复 AI 智能体页面在 `/agent?conversation_id=` 路由下切换会话导致页面卡住的问题。该版本优化 URL `conversation_id` 与前端 `activeConversationId` 的同步逻辑，避免 query 更新与加载 effect 形成死循环；同时增加请求取消、过期请求忽略、轮询清理和大结果折叠渲染，保证 AI 智能体会话切换、任务状态恢复、取消、重试、下载能力稳定可用。

## 项目定位

meizhaiseek 是面向电商经营全链路的 AI 平台，目标是把运营问答、智能体任务、知识库检索、数据清洗、竞品分析和本地 Agent 能力统一到一个可登录、可审计、可恢复的工作台中。

平台采用 FastAPI 后端和 Next.js 前端。用户通过登录进入系统后，可以在不同模块中完成 AI 问答、智能体任务提交、知识库管理、数据集清洗、Connector 联调和后台账号治理。系统保持轻量本地化，不依赖 MySQL、PostgreSQL、Redis、MongoDB 或外部向量数据库。

## 主导航

- AI对话
- AI智能体
- AI创作
- 无限画板
- 竞品分析
- 美宅BI
- 万能美虾

## 第一版范围

- 前端使用 Next.js、TypeScript、Tailwind CSS，提供中文 SaaS 风格界面。
- 后端使用 FastAPI，提供健康检查、智能体列表、技能模板、文件上传、文件预览、任务创建、任务轮询、取消、重试和安全下载。
- 早期任务、配置、技能模板和文件记录使用本地 JSON 保存，v1.5.7 起逐步迁移到 APP SQLite。
- 前端不直接调用具体子 agent，只调用统一任务接口。

## AI 智能体模块说明

AI 智能体模块是平台核心工作台。用户可以选择智能体、选择技能模板、上传文件、预览输入文件、填写提示词并提交任务。后端 Orchestrator 根据 `agent_type` 分发到对应 workflow，任务状态写入平台存储，前端轮询展示进度、日志、结果和文件下载。

## 核心原则

- 用户数据必须按 `user_id` 隔离。
- admin/operator/viewer 权限保持清晰边界。
- DeepSeek API Key 只允许从后端环境变量读取，不能进入前端、日志或审计明文。
- RAG SQLite 只负责知识库 documents/chunks/embedding。
- APP SQLite 负责平台运行数据，不能与 RAG SQLite 混用。
- 旧 JSON 数据迁移前必须备份，不允许直接删除。
- 前端接口异常不能白屏，后端异常需要返回中文可读错误。

## 版本演进

### v0.1：基础页面

完成基础 AI 智能体页面、登录页和项目骨架。

### v0.2：视频脚本拆解展示

完成视频脚本拆解专用面板的前端展示，包括视频链接、上传入口、消耗展示和 mock 回复。

### v0.3：主导航路由

打通 AI 对话、AI 智能体、AI 创作、无限画板、竞品分析五个展示入口，隐藏用户名和历史会话。

### v0.4：智能体选择弹窗

AI 智能体页面支持 22 个智能体选择弹窗，选择视频脚本拆解后切换到专用面板。

### v0.5：多 Agent 协作任务中心

平台开始支持统一 agent run 任务中心。前端提交 agent run，后端 Orchestrator 根据 `agent_type` 调度 workflow。视频脚本拆解支持上传本地视频、返回本地路径、手动提示词、任务轮询、日志展示和结果文件路径展示。

### v0.6：可联调 Agent Run 系统

任务中心支持 `LOCAL_AGENT_MODE=http/cli/mock`、任务取消、任务重试、最近任务列表、Excel 文件下载、安全下载校验和输出文件统一管理。

### v0.7：本地视频脚本拆解 agent 协议化接入

视频脚本拆解升级为本地智能体能力协议化接入。meizhaiseek 平台不重复实现视频拆解算法，而是负责任务中心、参数配置、文件管理、结果展示、下载与质检反馈。本地视频脚本拆解 agent 作为核心拆解引擎，固定会话 ID 为 `019dd824-f4bb-7273-8ac3-6e19b195ff82`。

### v0.8：多智能体统一任务入口

平台从单一视频脚本拆解智能体扩展为多智能体统一任务入口。视频脚本拆解继续使用专用 workflow，其他智能体先通过 `generic_agent_workflow` 打通接口。前端新增智能体搜索、分类、通用任务面板、通用文件上传和任务状态交互优化。

### v0.9：多智能体配置与技能模板

新增智能体配置中心、技能模板中心、文件解析预览能力，并为竞品分析、智能选款、详情页策划、主图拆解四类重点智能体搭建专用 workflow 雏形。隐藏的 `competitor_analysis` 后端 agent_type 可被 workflow 使用，但不进入前端 22 个智能体选择列表。

### v1.0：后台配置治理与稳定性增强

v1.0 重点解决 runtime 配置污染、坏 JSON、任务僵尸状态、mock 场景不足、debug payload 不可追踪等问题。新增配置守卫、自动备份、自动修复、配置重置、运行时健康检查、任务自检、任务清理、Debug Payload 记录与回放、文件预览缓存和前端容错。

### v1.1：前端登录与展示文案整理

v1.1 新增前端本地登录能力，默认管理员账号为 `admin`，密码为 `admin123`。同时清理前台展示文案，隐藏左侧额度模块，删除开发期版本后缀字样，并将左侧导航更名为“美宅BI”和“万能美虾”。

### v1.2：后端鉴权与用户隔离

v1.2 将开发期前端固定登录升级为后端用户存储、PBKDF2 密码校验和 HMAC token 鉴权。系统支持 admin、operator、viewer 三种角色，使用 `auth_version` 在改密后立即使旧 token 失效，并记录登录、任务、文件、下载和管理操作审计日志。新任务、上传文件、结果 artifact 与 debug payload 按用户目录隔离。

### v1.3：本地 Agent 接入管理与联调中心

v1.3 新增本地 Agent Connector 管理。管理员可以配置 mock、HTTP、CLI 模式以及 base URL、endpoint、session ID、payload style 和 timeout；智能体配置可绑定 `connector_id`，任务执行优先使用绑定连接器。后端新增连接测试、payload 预览、Debug Payload 列表、详情、复制和重放。

### v1.4：账号管理与后台滚动治理

v1.4 新增管理员账号管理控制台。管理员可以新增用户、启用或禁用用户、修改角色与备注、重置密码，并查看指定用户的任务。系统明确落地 admin、operator、viewer 权限。审计日志支持按操作、状态和用户筛选，并可导出 CSV 或 JSONL。

### v1.5：Excel 字段映射与电商数据清洗中心

v1.5 新增用户隔离的 Dataset 中心。用户可以将上传的 XLSX、XLS 或 CSV 创建为 Dataset，系统自动识别字段并给出建议映射，确认映射后按重复链接、价格、成交金额和费比规则执行清洗。输出 `cleaned_data.xlsx`、`excluded_data.xlsx`、`data_profile.json` 和 `metrics_summary.json`。

### v1.5.1：AI 智能体会话持久化修复

v1.5.1 修复 AI 智能体任务会话持久化问题。用户在 `/agent` 提交任务后，系统自动创建 conversation，并生成 user/assistant 消息。左侧聊天记录从后端 `/api/conversations` 加载，切换路由或刷新页面后可以恢复智能体、prompt、messages、latest_run_id、任务状态和结果。

### v1.5.2：AI 对话首屏问答功能

v1.5.2 完成截图所示 AI 对话首屏问答功能。系统使用 FastAPI 提供问答接口，本地 bge-small-zh 负责中文向量化，SQLite 作为轻量 RAG 存储，DeepSeek v4 Flash 负责实时回答。AI 对话记录会持久化保存，并显示在页面中间左侧的 AI 对话二级聊天栏。

### v1.5.3：AI 对话知识库入库与 RAG 管理中心

v1.5.3 新增知识库文档入库与 RAG 管理能力。用户可以在 AI 对话页面打开知识库面板，上传 txt、md、docx 文档，系统解析文本、切分 chunk、使用 bge-small-zh 生成 embedding，并写入 SQLite RAG 库。

### v1.5.4：会话栏交互优化版

v1.5.4 优化 AI 对话和 AI 智能体页面的二级会话栏交互。AI 对话记录和 AI 智能体会话记录支持删除，删除采用软归档方式并进行二次确认。二级会话栏支持收缩与展开，收缩状态会保存到本地。

### v1.5.5：本地模型状态与 RAG 可用性诊断

v1.5.5 新增 bge-small-zh 模型状态检测、Embedding 测试、RAG 检索测试和知识库诊断能力。用户可以在知识库面板中查看本地模型路径、模型是否存在、是否可加载、SQLite 文档和 chunk 数量、DeepSeek 配置状态，并通过诊断按钮定位 RAG 不可用原因。

### v1.5.6：AI 对话流式输出与回答体验优化

v1.5.6 在 AI 对话、知识库和 RAG 诊断能力基础上，新增 DeepSeek 流式输出能力。用户在 `/chat` 发送问题后，系统先显示检索状态，再实时输出回答内容，并在回答完成后持久化到 QA 会话。该版本保留非流式接口作为 fallback，同时增加停止生成、sources 折叠展示、warnings 展示、复制回答、重新生成等交互优化。

### v1.5.7：文档乱码修复与 SQLite 存储底座迁移

v1.5.7 修复 `docs/API.md` 和 `docs/PRD.md` 的中文乱码，并新增独立 APP SQLite 作为平台运行数据主存储。APP SQLite 用于用户账号、权限、审计日志、QA 会话、AI 智能体会话、agent runs、Connector、Debug Payload、文件和 artifact metadata；RAG SQLite 继续只用于知识库 documents/chunks/embedding。系统启动时初始化 APP SQLite，按需把旧 JSON 数据备份并迁移到 SQLite，接口返回结构保持不变。

## 存储边界

- `APP_SQLITE_PATH`：平台运行数据，默认 `apps/api/runtime/app/meizhaiseek.sqlite3`。
- `RAG_SQLITE_PATH`：知识库向量数据，默认 `apps/api/runtime/rag/rag.sqlite3`。
- `APP_JSON_LEGACY_BACKUP_DIR`：旧 JSON 备份目录，默认 `apps/api/runtime/legacy_json_backups`。

APP SQLite 和 RAG SQLite 分开管理。APP SQLite 不保存 embedding；RAG SQLite 不保存账号、审计、会话或任务运行状态。

## 后续计划

- v1.6：视频拆解智能体生产化。
- v1.7：智能体蓝图与方法论配置中心。
- v1.8：参考项目拆解助手。

### v1.6：视频拆解智能体生产化

v1.6 将已部署的本地视频拆解 Agent 产品化为平台第一个正式业务智能体。该版本新增本地 Agent 连接状态检测、提交前预检、视频拆解专用输入区、高级拆解参数、任务步骤状态、结构化结果面板、镜头时间轴、字幕 OCR、卖点识别、视觉证明帧、质量警告和输出文件管理。视频拆解任务、结果、文件、artifact 和 Debug Payload 均写入 APP SQLite，并支持刷新恢复、下载、预览、取消和重试。
