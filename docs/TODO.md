# TODO
## v1.7.1 已完成目标

- 蓝图结构化编辑器。
- 输入协议编辑器。
- 方法论步骤编辑器。
- Prompt 编辑器。
- 执行配置编辑器。
- 输出协议编辑器。
- 高级 JSON 编辑保留。
- 输入表单预览。
- 结果结构预览。
- `agent_blueprint_test_runs`。
- `agent_blueprint_validation_results`。
- 测试运行历史。
- 验证结果历史。
- 蓝图版本差异。
- 发布质量门禁。
- 回滚差异确认。
- 视频拆解蓝图发布闭环。
- `/agent` 蓝图信息轻量展示。
- Blueprint SWR hooks。
- Blueprint 自动化测试。
- 文档更新。

## v1.7 已完成目标

- Agent Blueprint SQLite 表。
- Agent Blueprint Store。
- Agent Blueprint Service。
- Blueprint Validator。
- Blueprint Import/Export。
- 生命周期状态管理。
- 输入协议配置。
- 方法论步骤配置。
- Prompt 版本配置。
- 执行配置。
- 输出协议配置。
- 结果 UI 配置。
- 测试用例。
- 验收规则。
- 发布与回滚。
- 复制蓝图。
- 导入预览。
- 导入与导出。
- Agent Registry 关联。
- 视频拆解样板蓝图。
- 蓝图管理前端。
- Blueprint 权限控制。
- Blueprint 审计日志。
- Blueprint 自动化测试。
- 文档更新。

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

- v1.7.1：视频拆解蓝图迁移与发布闭环优化。
- v1.8：参考项目拆解与蓝图生成助手。
- v1.9：基于蓝图实现第一个非视频业务智能体。
- v2.0：多智能体工作流编排。
- 继续把低风险读取接口接入 SWR，避免把提交类接口改成缓存模型。
- 观察 Agent Run SSE 的稳定性，再决定是否降低 polling 频率。
- legacy JSON fallback 保持关闭，确认长时间稳定后再考虑移除更多旧路径。
- 视频拆解链路继续补充更多失败样例和 artifact 边界测试。

