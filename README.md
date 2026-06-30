# meizhaiseek-platform

meizhaiseek-platform 是一个电商 AI 智能分析平台的第一版骨架。当前版本包含 Next.js 前端、FastAPI 后端、mock 智能体数据和 mock 对话接口。

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

## 环境变量

复制 `.env.example` 后按本地环境调整。

```bash
cp .env.example .env
```

前端读取 `NEXT_PUBLIC_API_BASE_URL` 调用后端。默认管理员由环境变量初始化，首次启动可使用 `admin / admin123` 登录；已有用户文件不会被初始密码覆盖。
