# 视频拆解 Agent 接入说明

## 本地启动
```powershell
cd E:\USE\codexhome\fenge
.\start_agent_8001.bat
```

默认地址：
- Base URL: `http://127.0.0.1:8001`
- Health: `GET /health`
- Run: `POST /run`
- Docker 内访问宿主机 8001 时使用：`http://host.docker.internal:8001`

主平台默认 Connector 为 `video_script_agent`，默认 `base_url=http://127.0.0.1:8001`、`health_path=/health`、`endpoint=/run`、`timeout_seconds=1800`。用户可在 Connector 管理中修改，平台不会让前端直连 8001。

## Health 示例
```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/health"
```

成功时平台状态接口 `GET /api/agents/video-script/status` 会返回 `connected`，并透出 `status=ok`、`service`、`version`、`model_version=shot_cutting_agent_v2_19_reference_balanced_fast_proof`。

## Mock Payload
```json
{
  "mode": "mock"
}
```

## shot_text_excel Payload
```json
{
  "mode": "shot_text_excel",
  "video_file": "E:\\USE\\codexhome\\fenge\\videos\\test\\1.mp4",
  "output_dir": "E:\\USE\\codexhome\\fenge\\output\\test",
  "subtitle_region": "bottom",
  "ocr_workers": 6
}
```

平台字段映射：
- `video_path` / `video_file` -> `video_file`
- `output_dir` -> `output_dir`
- `standard` / `standard_breakdown` / `shot_text_excel` -> `shot_text_excel`
- `mock` -> `mock`
- `subtitle_region` 默认 `bottom`
- `ocr_workers` 默认 `6`

`enable_ocr`、`export_excel`、`export_json`、`export_keyframes`、`enable_quality_check`、`keep_debug_payload` 只保留在平台 run/debug 配置中，不直接传给本地 Agent，避免未知字段导致本地 Agent 拒绝请求。

## 产物
真实测试默认输出：
- Excel: `E:\USE\codexhome\fenge\output\test\shot_text_excels\1_shot_text.xlsx`
- shot_report: `E:\USE\codexhome\fenge\output\test\1\model_optimized\model_optimized_shot_report.json`

平台会登记允许扩展名的产物：`.xlsx`、`.json`、`.txt`、`.md`、`.png`、`.jpg`、`.jpeg`、`.webp`，并为输出目录生成 `folder_manifest.json`。Artifact 下载继续校验登录用户、run 归属和安全路径。

## 常见失败
- 8001 未启动：状态为 `disconnected`；提交任务后平台真实 failed，不伪造成 completed。
- 视频路径不存在：本地 Agent 返回失败，平台回写 run、conversation 和 assistant message。
- 输出目录不可写：任务 failed，Debug Payload 可查看 request/error。
- Docker 调用宿主机 8001：Connector Base URL 改为 `http://host.docker.internal:8001`。
