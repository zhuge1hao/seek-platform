# AGENT Performance Notes

## v1.6.2 排查结论

- `/agent` 卡顿的主要风险不是 URL 同步，而是会话详情和轮询默认带完整 `result_json`，前端 JSON parse 与结果面板渲染会阻塞主线程。
- v1.6.2 将会话详情和轮询改为轻量 summary，完整 result 只在用户展开结果 Tab 时加载。
- Debug Payload 不参与会话切换，只在后台 Debug Payload 详情中按需读取。
- Artifact 切换时只展示 metadata，下载或预览由用户点击触发。

## 验证方法

- 打开浏览器 Performance 面板，快速点击多个 `/agent` 会话，观察主线程长任务是否显著减少。
- Network 面板中，切换会话应只出现 conversation detail；running 任务只出现单一路径 `/api/agent-runs/{run_id}/summary` 轮询。
- 切换到视频拆解结果 Tab 时，才应出现 `/api/agent-runs/{run_id}/result`。
- 开发环境中超过 80ms 的 `agent.loadConversation`、`agent.fetchConversation`、`agent.pollRun`、`agent.videoResult.prepare` 会输出 `[perf]` 日志。
