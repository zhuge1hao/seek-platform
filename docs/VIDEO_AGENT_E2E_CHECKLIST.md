# Video Agent E2E Checklist

## 前置条件

- API: `http://127.0.0.1:8000`
- Web: `http://localhost:3000`
- 本地视频 Agent: `http://127.0.0.1:8001`
- 测试视频：`E:\USE\codexhome\fenge\videos\test\1.mp4`
- 输出目录：`E:\USE\codexhome\fenge\output\test`

## 手动检查

1. 打开 `/agent`。
2. 选择视频拆解智能体。
3. 点击测试连接，确认状态为 connected，`model_version` 为 `shot_cutting_agent_v2_19_reference_balanced_fast_proof`。
4. 点击使用测试视频，确认填入 video file、output dir、subtitle region 和 ocr workers。
5. 打开 Payload 预览，确认最终 request 只包含本地 Agent 支持字段。
6. 提交任务并等待 completed。
7. 确认结果面板展示 raw shot count、model optimized shots、Excel columns/images、Excel path、shot report path。
8. 确认 artifact 列表包含 Excel、shot report 和 folder manifest；图片存在时可预览。
9. 刷新页面和切换路由后，结果仍可恢复。

## 自动 smoke

```powershell
python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent
```

不带 `--require-video-agent` 时，8001 不可达应输出 SKIP。

## 成功标准

- `/api/agents/video-script/status` 返回 connected。
- run status 为 completed。
- conversation status 为 completed。
- assistant message 包含 completed summary。
- result_json.summary 字段可读取。
- artifacts 可下载或预览。
