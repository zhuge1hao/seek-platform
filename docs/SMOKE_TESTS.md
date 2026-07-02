# Smoke Tests

## 启动服务

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

默认 API 地址为 `http://127.0.0.1:8000`，可用环境变量覆盖：

```powershell
$env:API_BASE_URL='http://127.0.0.1:8000'
$env:SMOKE_ADMIN_USERNAME='admin'
$env:SMOKE_ADMIN_PASSWORD='<local-password>'
python apps/api/scripts/smoke_minimal.py
```

脚本不硬编码生产密码。缺少密码时会给出清晰提示并失败。

## 覆盖范围

- `GET /health`
- 登录 admin
- `GET /api/admin/runtime/health`
- `GET /api/conversations`
- `POST /api/agent-runs`
- conversation、agent_messages、agent_runs 持久化检查
- storage health
- QA model status
- 8001 未启动时任务真实 failed

## 视频 Agent E2E

默认 smoke 不依赖 8001。可选执行：

```powershell
$env:VIDEO_AGENT_BASE_URL='http://127.0.0.1:8001'
$env:VIDEO_AGENT_TEST_VIDEO='E:\USE\codexhome\fenge\videos\test\1.mp4'
$env:VIDEO_AGENT_TEST_OUTPUT_DIR='E:\USE\codexhome\fenge\output\test'
python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent
```

不带 `--require-video-agent` 时，8001 不可达会标记 SKIP。带上该参数时不可达会 FAIL。

## GitHub Actions

CI 运行 compileall、unittest 和前端 build。需要真实服务的 smoke 不在 CI 中强制执行。
