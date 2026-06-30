# meizhaiseek-platform v1.5.7 架构评审报告

> 评审日期：2026-06-28
>
> 版本：v1.5.7

---

## 总体评价

作为面向小团队、本地部署的电商 AI 分析平台，这是一个**务实且质量不错的架构**。它不是大厂的微服务架构，也不需要是——8 个 Python 依赖、0 个外部数据库、一个 `start-dev.ps1` 就能跑起来，这种"简洁"本身就是一种架构取舍。v1.5.7 的 SQLite 迁移是关键升级，整体质量属于**中上水平**。

---

## 一、版本演进路线

| 版本 | 核心变更 |
|------|----------|
| v1.5.1 | `/agent` 会话持久化，Conversation API，任务状态回写 |
| v1.5.2 | AI 对话首屏问答（RAG + DeepSeek） |
| v1.5.3 | 知识库文档入库/管理（txt/md/docx） |
| v1.5.4 | 会话栏交互优化（软删除/收缩/二次确认） |
| v1.5.5 | BGE 模型诊断 + RAG 可用性检测 |
| v1.5.6 | DeepSeek 流式输出（SSE） |
| **v1.5.7** | **文档乱码修复 + APP SQLite 存储底座迁移** |

---

## 二、架构全景图

### 2.1 项目结构

```
meizhaiseek-platform/
├── apps/
│   ├── api/                         # FastAPI 后端 v1.5.7
│   │   ├── main.py                  # 入口 | 启动时初始化 SQLite + 自动迁移
│   │   ├── routers/  (15个)         # HTTP API 路由层
│   │   ├── services/  (40+个)       # 业务逻辑层
│   │   ├── schemas/  (3个)          # Pydantic 请求/响应模型
│   │   ├── workflows/ (6个 + 5步骤)  # 工作流编排
│   │   ├── models/bge-small-zh/     # 本地 Embedding 模型
│   │   ├── runtime/                 # 运行时数据
│   │   └── uploads/                 # 上传文件
│   │
│   └── web/                         # Next.js 14 前端
│       └── src/
│           ├── app/       (8个页面)   # App Router
│           ├── components/ (30+个)    # UI 组件
│           └── lib/       (6个工具)   # API client, auth, etc.
│
├── docs/                            # 产品与技术文档
├── .env / .env.example
├── start-dev.ps1 / start-dev.bat
├── README.md
└── AGENTS.md
```

### 2.2 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Next.js 14 (App Router) + React 18 |
| 前端样式 | Tailwind CSS 3.4 + Lucide React |
| 后端框架 | FastAPI 0.115.6 + Uvicorn 0.34.0 |
| 数据校验 | Pydantic (built-in FastAPI) |
| 存储 | **SQLite 3** (WAL 模式) + JSON/JSONL 文件 |
| AI 推理 | DeepSeek API (deepseek-v4-flash) |
| 向量模型 | BGE-small-zh (sentence-transformers 3.3.1) |
| 表格处理 | openpyxl 3.1.5 + xlrd 2.0.1 |
| 文档解析 | python-docx 1.1.2 |
| 认证 | PBKDF2 密码 + HMAC JWT token |
| 编程语言 | Python 3.12 + TypeScript 5.7 |

---

## 三、核心架构决策

### 3.1 JSON → SQLite 存储迁移（v1.5.7 核心变更）

之前所有运行时数据用 JSON/JSONL 文件存储，v1.5.7 引入 **APP SQLite** 作为平台运行数据主存储。

#### 双 SQLite 边界

```
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│        APP SQLite               │  │        RAG SQLite               │
│  apps/api/runtime/app/          │  │  apps/api/runtime/rag/          │
│  meizhaiseek.sqlite3            │  │  rag.sqlite3                    │
│                                 │  │                                 │
│  · users                        │  │  · documents (知识库文档)       │
│  · audit_logs                   │  │  · chunks (文本块)              │
│  · qa_conversations             │  │  · embedding (向量)             │
│  · qa_messages                  │  │                                 │
│  · agent_conversations          │  │  只存知识库向量，               │
│  · agent_messages               │  │  不存账号/任务                  │
│  · agent_runs                   │  │                                 │
│  · local_agent_connectors       │  │                                 │
│  · debug_payloads               │  │                                 │
│  · files                        │  │                                 │
│  · artifacts                    │  │                                 │
│  · app_kv                       │  │                                 │
│  · schema_migrations            │  │                                 │
│                                 │  │                                 │
│  只存平台运行数据，              │  │                                 │
│  不存 embedding                  │  │                                 │
└─────────────────────────────────┘  └─────────────────────────────────┘
```

**切分理由**：两类数据的读写模式完全不同。APP SQLite 以 OLTP 增删改查为主，需要事务一致性；RAG SQLite 以向量相似度检索为主，读写不频繁但数据量大。合在一起会导致向量膨胀拖慢事务、事务锁阻塞检索。

#### 迁移流程

```
服务启动 (on_event startup)
  │
  ├─ init_app_db()
  │   ├─ 创建 SQLite 连接（WAL 模式，foreign_keys=ON）
  │   └─ run_migrations() → 执行 CREATE TABLE IF NOT EXISTS（13张表 + 12个索引）
  │
  └─ 如果 APP_SQLITE_AUTO_MIGRATE=true 且未迁移
      ├─ backup_legacy_json() → 备份到 legacy_json_backups/{timestamp}/
      ├─ 逐表幂等迁移（INSERT OR IGNORE / ON CONFLICT）
      └─ 写入 app_kv.json_migration_report
```

#### 兼容读取策略

所有服务**优先读 SQLite**，找不到时 **fallback 读旧 JSON 并自动写回 SQLite**。这意味着即使迁移漏了数据，系统能自愈。

#### 已迁移服务矩阵

| 服务 | 主要表 | 迁移方式 |
|------|--------|----------|
| `user_store.py` | `users` | 全量 upsert |
| `audit_log_service.py` | `audit_logs` | 逐条 INSERT OR IGNORE |
| `qa_conversation_store.py` | `qa_conversations` + `qa_messages` | bulk delete + insert |
| `conversation_store.py` | `agent_conversations` + `agent_messages` | bulk delete + insert |
| `task_store.py` | `agent_runs` | ON CONFLICT upsert |
| `agent_connector_store.py` | `local_agent_connectors` | ON CONFLICT upsert |
| `debug_payload_service.py` | `debug_payloads` | ON CONFLICT upsert |
| `file_store.py` | `files` | ON CONFLICT upsert |

#### 仍使用 JSON 的模块

| 模块 | 原因 |
|------|------|
| `dataset_store.py` | 数据集仍用 `datasets.json`（存在目录关联的复杂文件结构） |
| `agent_config_store.py` | 配置类数据保留 `agent_configs.json` |
| `skill_template_service.py` | 模板保留 `skill_templates.json` |

### 3.2 分层架构

```
routers/   →  HTTP 层，只做参数校验、鉴权、调用 service
services/  →  业务逻辑，不感知 HTTP 对象
schemas/   →  Pydantic 模型，请求/响应结构统一
workflows/ →  编排层，组合多个 service 完成复杂任务
```

这是 FastAPI 社区的推荐模式。路由不写业务逻辑，服务不碰 HTTP 对象，职责边界清楚。

### 3.3 安全模型

| 机制 | 实现 |
|------|------|
| 用户隔离 | 所有数据路径按 `user_id` 分区 |
| 角色权限 | admin > operator > viewer（viewer 只读） |
| 密码安全 | PBKDF2 哈希 + auth_version 递增 |
| 凭证脱敏 | 审计日志/Debug Payload 全程 `_redact()` 过滤 password/token/api_key |
| 下载安全 | 安全目录校验 + 文件所有权校验，双重验证 |
| Token | HMAC JWT，环境变量配置 secret 和过期时间 |

---

## 四、设计亮点

### 4.1 迁移工程做得扎实

```
备份 → 幂等写入 → 报告 → 兼容读取（SQLite fallback JSON）
```

- **不删除源文件**：即使迁移出错了，旧 JSON 还在
- **幂等设计**：`INSERT OR IGNORE` + `ON CONFLICT DO UPDATE`，重复执行不产生脏数据
- **兼容读取**：每个服务先查 SQLite，找不到再 fallback 读 JSON 并自动写回
- **全量备份**：迁移前完整复制 `runtime/` 下所有 JSON/JSONL/TXT 到 `legacy_json_backups/{timestamp}/`

### 4.2 可运维性设计完善

- Config 的 **backup / repair / reset** 三条路径
- **Zombie 任务自动回收**（`agent_run_maintenance`）
- **运行健康检查**返回 warnings 列表，而非简单的 ok/fail
- **审计日志**支持条件筛选和 CSV/JSONL 双格式导出
- **Debug Payload** 支持 request/response 查看和 replay 重放
- **RAG 诊断**链路：模型状态 → Embedding 测试 → 检索测试 → 综合诊断

### 4.3 安全意识有底线

很多内部项目在这些点上直接跳过，这个项目至少在关键路径上没有妥协：

- 用户隔离不是"检查一下"，而是存储路径本身就按用户分
- 审计日志全程脱敏
- 文件下载双重校验（路径安全 + 所有权）
- local agent 不可达时真实 failed，不伪造成功
- 前端不允许直连 local agent

---

## 五、可改进项

### 5.1 ⚠️ 写入模式：DELETE + 全量 INSERT 太重

**位置**：`conversation_store.py` 和 `qa_conversation_store.py` 的 `_write()` 函数

```python
def _write(user_id, items):
    with conn:
        conn.execute("DELETE FROM agent_messages WHERE user_id=?", ...)
        conn.execute("DELETE FROM agent_conversations WHERE user_id=?", ...)
        for conversation in items:       # 全部重新 INSERT
            ...
            for message in ...
```

**问题**：每次追加一条消息，都会删除该用户全部会话和消息，再逐条写回。单用户积累几百个会话、几千条消息后，这个操作会越来越慢。

**建议**：改为增量 upsert——新增/修改单条记录，只在全量替换场景（如 legacy 导入）才用 bulk write。

### 5.2 ⚠️ dataset_store 未迁移，存储方案不一致

**问题**：

- 查询数据集列表时每次都要 `json.loads` 整个文件
- 跨用户查询（admin 功能）需要遍历所有用户目录
- 与 task_store（已 SQLite）之间的 `dataset_ids` 关联无法做 JOIN

**建议**：下一版本把 dataset 也迁入 APP SQLite，可以和 agent_runs 做关联查询。

### 5.3 ⚠️ 缺少依赖注入，存在循环导入风险

**位置**：`task_store.py`

```python
def _write_run(run):
    ...
    if run.get("conversation_id"):
        from services import conversation_store  # 函数内延迟导入
        conversation_store.sync_run(run)
```

**问题**：`task_store` ↔ `conversation_store` 互相引用，靠函数内 `import` 来避免循环。一两个还能接受，但如果后续 service 之间关联增多，这会变成维护负担。

**建议**：引入一个轻量的事件钩子或回调注册机制，让 `task_store` 不直接知道 `conversation_store` 的存在——比如 `on_run_updated` 回调列表。

### 5.4 ⚠️ 前端缺少数据获取层

**问题**：每个组件直接裸用 `fetch`，没有 SWR / TanStack Query：

- 没有请求去重（两个组件同时 mount 会发两次同样的请求）
- 没有自动重试
- 缓存策略靠手动管理
- 轮询逻辑每个组件自己写

**建议**：引入 `swr`（Vercel 出品，和 Next.js 同源，约 2KB）或 `@tanstack/react-query`。

### 5.5 ⚠️ 没有异步 I/O

**问题**：FastAPI 原生支持 `async/await`，但所有 service 都是同步函数。

**分析**：

- SQLite 本身是同步的，所以主存储路径不变的话，收益有限
- 但如果将来需要并发调用外部 API（DeepSeek + local agent），同步代码会成为瓶颈

**建议**：如果并发量不大可以保持现状；如果后续考虑提升吞吐，可以把 I/O 密集的操作（DeepSeek 调用、HTTP connector 调用）改为 `async`，用 `asyncio.to_thread` 包裹 SQLite 操作。

### 5.6 ⚠️ 安全配置使用明文默认值

```env
AUTH_TOKEN_SECRET=meizhaiseek-dev-secret
MEIZHAISEEK_ADMIN_INITIAL_PASSWORD=admin123
```

作为内部开发环境可以接受，但如果要部署给多人使用，建议改为生成式初始化或在首次启动时要求修改。

---

## 六、综合评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 分层架构 | ★★★★☆ | routers/services/schemas/workflows 分层清晰 |
| 数据建模 | ★★★★☆ | SQLite Schema 设计合理，索引覆盖查询路径 |
| 数据安全 | ★★★★☆ | 用户隔离、凭证脱敏、审计都到位 |
| 可运维性 | ★★★★★ | backup/repair/reset/health/migration/debug 一应俱全 |
| 代码一致性 | ★★★☆☆ | 迁移不完全（dataset 未迁）、写入模式可优化 |
| 前端架构 | ★★★☆☆ | 组件拆分合理，但缺数据层抽象 |
| 扩展性 | ★★☆☆☆ | SQLite 单机、同步 I/O，适合 < 50 并发用户 |

---

## 七、后续优化优先级

| 优先级 | 事项 | 预期收益 |
|--------|------|----------|
| P0 | 优化增量写入（conversation_store / qa_conversation_store） | 消除单用户数据量大时的性能退化 |
| P1 | dataset_store 迁入 APP SQLite | 统一存储方案，支持关联查询 |
| P1 | 引入事件钩子消除循环导入 | 提升服务间解耦度 |
| P2 | 前端引入 SWR 或 TanStack Query | 减少冗余请求，统一状态管理 |
| P2 | DeepSeek 调用改为 async | 提升并发吞吐 |
| P3 | 安全配置生成式初始化 | 生产部署安全加固 |

---

## 八、结论

v1.5.7 的 SQLite 迁移是平台架构的一次关键升级。双 SQLite 边界划分合理，迁移过程设计严谨（备份→幂等→兼容），可运维性设计突出。当前架构完全适合小团队本地部署场景。

后续重点建议放在**统一存储方案**（dataset 迁入 SQLite）和**优化写入性能**（改增量为 upsert），这两项在数据量增长后会首先成为瓶颈。前端的架构问题暂时不影响功能，可以在业务需求稳定后再重构数据层。
