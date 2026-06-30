# 视频拆解 Agent 接入说明

## 默认连接
- 本地视频 Agent 默认地址：`http://127.0.0.1:8001`
- 默认 connector：`video_script_agent`
- 默认 session_id：`019dd824-f4bb-7273-8ac3-6e19b195ff82`

## 启动与测试
1. 先启动本地视频拆解 Agent，确认监听 `http://127.0.0.1:8001`。
2. 在平台进入 `/agent`，选择“视频拆解智能体”。
3. 点击“测试连接”，平台后端会检测本地 8001 是否可达，前端不会直连本地 Agent。

## 提交任务
- 可上传视频文件、填写本地视频路径或粘贴视频链接。
- 支持模式：标准视频拆解、无字幕视频拆解、快速拆解、质检拆解。
- 高级参数会写入 `workflow_options_json` 和 Debug Payload。

## 输出文件
- 输出文件登记到 APP SQLite `artifacts` 表。
- 支持 Excel、JSON、图片、folder manifest、质量报告和 Debug Payload。
- 文件本体仍在磁盘目录，下载前会校验用户和安全路径。

## 常见错误
- 8001 未启动：状态卡显示未连接；提交前会提示，仍然提交则任务真实 failed。
- 视频路径不存在：本地 Agent 返回失败后平台展示错误，并写入 run 和 conversation。
- 输出目录不可写：任务 failed，Debug Payload 可查看 request/error。
- OCR 失败或 Excel 未生成：结果面板显示已有步骤、质量警告和已收集文件。

## Debug Payload
- 后台 Debug Payload 可查看 request、response、error。
- Replay 会标记为重放，不覆盖原始 run。