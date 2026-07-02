# Codex Handoff

## 项目

- 名称：meizhaiseek-platform
- 当前版本：meizhaiseek v1.6.5
- 分支：main
- 仓库：https://github.com/zhuge1hao/seek-platform.git
- 路径：`E:\USE\codexhome\agents-cowork\meizhaiseek-platform`

## 启动

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

默认地址：

- API: http://127.0.0.1:8000
- Web: http://localhost:3000
- 日志：`apps/api/runtime/logs/`

## 验证

```powershell
python -m compileall apps/api
python -m unittest discover -s apps/api/tests
cd apps/web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run build
cd ..\..
python apps/api/scripts/smoke_minimal.py
```

如果 8001 视频 Agent 已启动：

```powershell
python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent
```

## 当前边界

- APP SQLite：运行数据、用户、审计、会话、任务、Connector、Debug Payload、Dataset metadata、artifact metadata。
- RAG SQLite：知识库 documents、chunks、embedding。
- 两个 SQLite 不合并。
- 不新增 MySQL、PostgreSQL、Redis、MongoDB。
- 不提交 `.env`、runtime 数据、generated secrets、logs、uploads、models、node_modules。

## 视频 Agent

默认 Connector：

- Base URL: `http://127.0.0.1:8001`
- Health Path: `/health`
- Run Path: `/run`
- Docker 内访问宿主机：`http://host.docker.internal:8001`

真实 E2E 使用：

- 视频：`E:\USE\codexhome\fenge\videos\test\1.mp4`
- 输出：`E:\USE\codexhome\fenge\output\test`

## v1.6.5 重点

- SWR 读取层扩大。
- 核心 unittest。
- legacy JSON fallback 默认关闭。
- Docker production compose。
- SQLite async wrapper 第一阶段。
- Agent Run SSE 与 polling fallback。
- 视频 Agent E2E smoke 增强。
