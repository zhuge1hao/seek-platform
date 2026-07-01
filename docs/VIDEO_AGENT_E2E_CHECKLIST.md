# 视频拆解 Agent E2E 验收清单

## 前置条件
- 主平台 API 在 `http://127.0.0.1:8000` 运行。
- 前端在 `http://127.0.0.1:3000` 运行。
- 本地视频 Agent 已启动：
  ```powershell
  cd E:\USE\codexhome\fenge
  .\start_agent_8001.bat
  ```
- 测试视频存在：`E:\USE\codexhome\fenge\videos\test\1.mp4`

## 手工验收
- 打开 `/agent`，选择视频拆解智能体。
- 点击“测试连接”，确认状态为 connected，`model_version` 为 `shot_cutting_agent_v2_19_reference_balanced_fast_proof`。
- 点击“使用测试视频”，确认填入：
  - `video_file=E:\USE\codexhome\fenge\videos\test\1.mp4`
  - `output_dir=E:\USE\codexhome\fenge\output\test`
  - `subtitle_region=bottom`
  - `ocr_workers=6`
  - `mode=shot_text_excel`
- 打开 Payload 预览，确认最终 request 只有本地 Agent 支持的字段：`mode`、`video_file`、`output_dir`、`subtitle_region`、`ocr_workers`。
- 提交任务并等待 completed。
- 确认结果面板显示 raw shot count、model optimized shots、Excel columns/images、Excel path、shot_report path。
- 确认 Artifact 列表包含 Excel、shot_report、`folder_manifest.json`，图片如存在可预览。
- 刷新页面、切换路由再回来，run 结果和 artifacts 能恢复。

## 自动 smoke
默认 smoke 不依赖 8001：
```powershell
python apps/api/scripts/smoke_minimal.py
```

真实视频 E2E：
```powershell
python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent
```

如果只传 `--video-agent-e2e` 且 8001 不可达，视频 E2E 应显示 SKIP；如果同时传 `--require-video-agent`，则应 FAIL。

## 验收标准
- `GET /health` 返回 `{"status":"ok","service":"meizhaiseek-api"}`。
- `/api/admin/runtime/health` 返回 `version=v1.6.4`。
- `/api/agents/video-script/status` 8001 可达时为 connected，不可达时为 disconnected 且不返回 500。
- completed 任务写入 APP SQLite：agent run、conversation、assistant message、debug payload、artifacts。
- 失败任务保留真实 error，不伪造成成功。
