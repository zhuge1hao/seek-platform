# meizhaiseek-platform

meizhaiseek-platform 是面向电商经营场景的本地轻量 AI 工作台。当前版本为 **meizhaiseek v1.7.1**，包含 Next.js 前端、FastAPI 后端、APP SQLite、RAG SQLite、AI 对话、AI 智能体、Dataset、Connector、Debug Payload、后台账号管理、视频拆解智能体产物闭环，以及智能体蓝图与方法论配置中心。

v1.7.1 在 v1.7 蓝图中心上补齐发布闭环：结构化编辑、验证历史、测试运行历史、版本差异、发布门禁、输入/结果预览和 `/agent` 蓝图摘要。Blueprint 仍只描述现有 Agent Registry、Workflow 与 Connector，不执行任意代码。

模型展示名保持为 **meizhaiseek 2.0**。

## 快速启动

推荐在项目根目录运行：

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

默认地址：

- Web: http://localhost:3000
- API: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- 日志目录: `apps/api/runtime/logs/`

也可以分别启动：

```powershell
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
cd apps/web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run dev
```

## 配置

复制 `.env.example` 后按本地环境调整。生产部署前请设置：

- `AUTH_TOKEN_SECRET`
- `MEIZHAISEEK_ADMIN_INITIAL_PASSWORD`
- `NEXT_PUBLIC_API_BASE_URL`

如果未设置 `AUTH_TOKEN_SECRET`，后端会在 `apps/api/runtime/app/generated_secrets.json` 生成本地 secret。该文件不应提交到 Git。

`APP_LEGACY_JSON_FALLBACK=false` 是默认推荐值。只有紧急恢复旧 JSON 数据时才临时设为 `true`。

## 测试

```powershell
python -m compileall apps/api
python -m unittest discover -s apps/api/tests
python -m pytest apps/api/tests
cd apps/web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run build
cd ..\..
python apps/api/scripts/smoke_minimal.py
```

如本地视频拆解 Agent 已启动，可运行：

```powershell
python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent
```

## Docker

开发模式：

```powershell
docker compose up --build
```

生产模式：

```powershell
docker compose -f docker-compose.prod.yml up --build -d
```

Docker 内访问宿主机视频 Agent 时，Connector Base URL 使用：

```text
http://host.docker.internal:8001
```

## 运行数据

- APP SQLite: `apps/api/runtime/app/meizhaiseek.sqlite3`
- RAG SQLite: `apps/api/runtime/rag/rag.sqlite3`
- 上传文件: `apps/api/uploads/`
- 日志: `apps/api/runtime/logs/`

这些运行时文件不应提交到 Git。

