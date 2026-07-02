# Video Agent Setup

## 本地 Agent

项目路径：`E:\USE\codexhome\fenge`

启动命令：

```powershell
cd E:\USE\codexhome\fenge
.\start_agent_8001.bat
```

健康检查：

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/health"
```

平台 Connector 默认配置：

- Base URL: `http://127.0.0.1:8001`
- Health Path: `/health`
- Run Path: `/run`
- Timeout: 1800 seconds

Docker 内访问宿主机 8001 时使用：

```text
http://host.docker.internal:8001
```

## mock payload

```json
{"mode":"mock"}
```

## shot_text_excel payload

```json
{
  "mode": "shot_text_excel",
  "video_file": "E:\\USE\\codexhome\\fenge\\videos\\test\\1.mp4",
  "output_dir": "E:\\USE\\codexhome\\fenge\\output\\test",
  "subtitle_region": "bottom",
  "ocr_workers": 6
}
```

## 平台行为

- 前端不直连 8001。
- 后端通过 Connector 检查 `/health` 并调用 `/run`。
- 8001 不可达时 run 必须 failed。
- completed 后写入 run、conversation、assistant message、Debug Payload 和 artifacts。
