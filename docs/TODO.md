# TODO

## v1.6.5 已完成目标

- 扩大 SWR 覆盖范围。
- 新增 `useAgentConnectors`、`useDebugPayloads`、`useDatasets`、`useFiles`、`useAgentConfigs`、`useSkills`、`useAdminUsers`。
- 新增 `docs/FRONTEND_DATA_LAYER.md`。
- 增加核心路径 unittest。
- 覆盖 auth、conversation_store、task_store、agent-runs、video_result_normalizer。
- 更新 smoke 与 testing 文档。
- 残留日志归档到 `apps/api/runtime/logs/archive/`。
- 新增 `APP_LEGACY_JSON_FALLBACK=false` feature flag。
- runtime health 显示 `legacy_json_fallback_enabled`。
- 新增 `docker-compose.prod.yml`。
- 新增 SQLite async wrapper 第一阶段。
- 新增 Agent Run SSE events 接口。
- 前端新增 `useAgentRunEvents`，保留 polling fallback。
- 增强 video-agent E2E smoke。
- GitHub Actions 更新。
- 本地服务启动验证。

## 后续建议

- 继续把低风险读取接口接入 SWR，避免把提交类接口改成缓存模型。
- 观察 Agent Run SSE 的稳定性，再决定是否降低 polling 频率。
- legacy JSON fallback 保持关闭，确认长时间稳定后再考虑移除更多旧路径。
- 视频拆解链路继续补充更多失败样例和 artifact 边界测试。
