# meizhaiseek-platform

meizhaiseek-platform 是一个面向电商经营全链路的本地 AI 工作台。当前版本为 meizhaiseek v1.6.3，包含 Next.js 前端、FastAPI 后端、APP SQLite、RAG SQLite、AI 对话、智能体任务、Dataset、Connector 和后台管理能力。

## 项目结构

```text
meizhaiseek-platform/
├─ apps/
│  ├─ web/
│  └─ api/
├─ docs/
│  ├─ PRD.md
│  ├─ API.md
│  └─ TODO.md
├─ README.md
├─ .env.example
└─ docker-compose.yml
```

## 前端启动

```bash
cd apps/web
npm install
npm run dev
```

默认访问：

- 登录页：http://localhost:3000/login
- AI 智能体页：http://localhost:3000/agent

## 后端启动

```bash
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

默认接口：

- 健康检查：http://localhost:8000/health
- 智能体列表：http://localhost:8000/api/agents
- 技能列表：http://localhost:8000/api/skills

## 一键启动

Windows 下可以在项目根目录双击：

```text
start-dev.bat
```

也可以在 PowerShell 中运行：

```powershell
.\start-dev.ps1
```

脚本会同时启动前端和后端：

- 前端：http://localhost:3000
- 后端：http://127.0.0.1:8000
- API 文档：http://127.0.0.1:8000/docs
- 日志目录：`apps/api/runtime/logs/`

## 环境变量

复制 `.env.example` 后按本地环境调整。

```bash
cp .env.example .env
```

前端读取 `NEXT_PUBLIC_API_BASE_URL` 调用后端。默认管理员由环境变量初始化；生产或多人部署前请设置 `AUTH_TOKEN_SECRET` 和 `MEIZHAISEEK_ADMIN_INITIAL_PASSWORD`。如果未设置 `AUTH_TOKEN_SECRET`，后端会在 `apps/api/runtime/app/generated_secrets.json` 生成本地 secret；该文件不应提交。

## Smoke 测试

```powershell
$env:API_BASE_URL='http://127.0.0.1:8000'
$env:SMOKE_ADMIN_USERNAME='admin'
$env:SMOKE_ADMIN_PASSWORD='<本地管理员密码>'
python apps/api/scripts/smoke_minimal.py
```

更多说明见 `docs/SMOKE_TESTS.md`。

## Docker 可选启动

Docker 仅作为本地开发的可选方式，不引入 MySQL、PostgreSQL、Redis、MongoDB 或外部数据库服务。

```bash
docker compose up --build
```

默认端口：

- Web: http://localhost:3000
- API: http://localhost:8000

运行数据挂载在 `apps/api/runtime/` 和 `apps/api/uploads/`。
