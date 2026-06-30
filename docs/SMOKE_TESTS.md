# Smoke Tests

## 启动服务

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

默认后端为 `http://127.0.0.1:8000`，前端为 `http://localhost:3000`。

## 运行

```powershell
$env:API_BASE_URL='http://127.0.0.1:8000'
$env:SMOKE_ADMIN_USERNAME='admin'
$env:SMOKE_ADMIN_PASSWORD='<本地管理员密码>'
python apps/api/scripts/smoke_minimal.py
```

未设置 `SMOKE_ADMIN_USERNAME` / `SMOKE_ADMIN_PASSWORD` 时，脚本会读取 `.env` 中的 `MEIZHAISEEK_ADMIN_USERNAME` / `MEIZHAISEEK_ADMIN_INITIAL_PASSWORD`。读取不到密码会直接 FAIL，不会误报通过。

## 覆盖范围

- `GET /health`
- 管理员登录
- `GET /api/admin/runtime/health`
- `GET /api/conversations`
- `POST /api/agent-runs`
- `GET /api/agent-runs/{run_id}/summary`
- `GET /api/conversations/{conversation_id}`
- SQLite `agent_runs`、`agent_conversations`、`agent_messages` 落表检查
- `GET /api/admin/storage/health`
- `GET /api/qa/model-status`

8001 本地视频 Agent 未启动时，smoke 会验证任务真实进入 `failed`，不会伪造成成功。

## 常见失败

- 后端未启动：确认 8000 端口和 `API_BASE_URL`。
- 登录失败：确认本地 `.env` 或 smoke 环境变量中的管理员账号密码。
- runtime version 不匹配：确认后端已重启并加载当前代码。
- 8001 已启动：smoke 不要求 failed，只检查任务有真实后端状态。

## GitHub Actions

当前 smoke 需要本地运行中的 API 服务和管理员账号，不在 CI 强制执行。CI 只执行 `compileall` 和前端 build，避免依赖 DeepSeek、BGE 模型或 8001 local agent。
