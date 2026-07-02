# Changelog Context

## v1.6.5

架构评估 P1-P3 二轮优化、回归测试与服务启动。

- 扩大 SWR 读取层覆盖。
- 新增核心 unittest。
- legacy JSON fallback 默认关闭。
- runtime health 增加 `legacy_json_fallback_enabled`。
- 新增 Docker production compose。
- 新增 SQLite async wrapper 第一阶段。
- 新增 Agent Run SSE events 接口与前端 fallback。
- 增强视频 Agent E2E smoke。

## v1.6.4

视频拆解智能体真实成功链路验收与产物闭环。

- Connector 默认指向本地 8001。
- 平台 payload 映射为本地 Agent `/run` 原生结构。
- completed 结果标准化为平台 result_json。
- Excel、shot report、图片和 folder manifest artifact 自动登记。
- 前端结果面板支持刷新恢复。

## v1.6.3

架构评估 P1-P3 优化与工程规范补齐。

- 引入 SWR 基础数据层。
- DeepSeek 非流式调用增加 async wrapper。
- 新增 smoke 脚本、Docker 配置、CI、安全 secret 生成式初始化。

## v1.6.2

AI 智能体页面卡顿深度优化。

- 会话切换性能优化。
- 大 result/debug payload 延迟加载。
- run summary/result 拆分。

## v1.5.7 - v1.6.1

- APP SQLite 迁移。
- Dataset metadata 统一到 APP SQLite。
- `/chat` 流式问答和知识库诊断。
- 视频拆解智能体生产化。
- `/agent` 会话切换稳定性修复。
