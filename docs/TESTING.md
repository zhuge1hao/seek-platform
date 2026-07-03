# Testing

## 本地测试

```powershell
python -m compileall apps/api
python -m unittest discover -s apps/api/tests
cd apps/web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run build
cd ..\..
python apps/api/scripts/smoke_minimal.py
```

## 视频 Agent E2E

```powershell
python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent
```

可配置变量：

- `API_BASE_URL`
- `SMOKE_ADMIN_USERNAME`
- `SMOKE_ADMIN_PASSWORD`
- `VIDEO_AGENT_BASE_URL`
- `VIDEO_AGENT_TEST_VIDEO`
- `VIDEO_AGENT_TEST_OUTPUT_DIR`

## 单元测试说明

`apps/api/tests` 使用 Python 标准 `unittest`。测试默认使用临时 SQLite 路径，不依赖 DeepSeek、BGE 模型或 8001 服务。

## 常见失败原因

- 后端未启动。
- 本地管理员密码未通过环境变量传入。
- 8001 未启动但指定了 `--require-video-agent`。
- 前端 build 未设置 `NEXT_PUBLIC_API_BASE_URL`。

## v1.7.1 验证命令

- `python -m compileall apps/api`
- `python -m unittest discover -s apps/api/tests`
- `python -m pytest apps/api/tests`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build`
- `python apps/api/scripts/smoke_minimal.py`

默认测试使用临时 SQLite，不依赖 8001、DeepSeek 或 BGE。真实视频 E2E 仍通过 `python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent` 手动执行。
