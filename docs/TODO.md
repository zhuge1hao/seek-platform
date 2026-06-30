# TODO

## v1.6.3 已完成目标

- 引入 SWR 基础数据获取层
- 新增 queryKeys 和读取型 hooks
- RuntimeHealth / Conversation / Knowledge 等低风险接口接入 SWR
- DeepSeek async_generate_answer 兼容层
- 保留 DeepSeek 同步调用兼容
- 新增最小 smoke 测试脚本
- 新增 docs/SMOKE_TESTS.md
- 根目录日志迁移到 runtime/logs
- .bak-v1.5.7 文档备份移动到 docs/archive
- 新增 security_config_service
- AUTH_TOKEN_SECRET 缺失时生成式初始化
- 默认 secret / 默认初始密码 health warning
- docker-compose 配置补齐
- GitHub Actions CI
- 本地验证通过
- GitHub commit/push

## v1.6.2 已完成目标

- `/agent` 会话切换深度性能优化
- 增加前端开发环境性能探针
- conversation detail payload 轻量化
- 大 `result_json` 延迟加载
- Debug Payload 延迟加载
- Artifact 内容懒加载
- Agent run polling 统一为单一 hook
- 移除重复 `setInterval`
- 快速切换会话过期请求忽略
- `listConversations` 刷新减少
- `VideoBreakdownResultPanel` Tab 化/折叠化
- timeline/subtitle/proof_frames 分段渲染
- 大 JSON 默认不直接渲染
- React.memo 与轻量派生数据优化
- 大 payload 不再阻塞首屏切换
- `/agent` 快速连续点击稳定性验证

## v1.6.1 已完成目标

- 修复 `/agent?conversation_id=` 切换卡死
- 修复 URL 和 activeConversationId 同步死循环
- 增加 conversation detail 请求 AbortController
- 增加过期请求忽略机制
- 修复 run polling 重复创建问题
- 切换会话时清理旧 polling
- 大 payload 默认折叠/截断，避免阻塞渲染
- 删除按钮阻止事件冒泡
- conversation 不存在时清理 URL 和 localStorage
- `/agent` 页面切换稳定性验证

## v1.6 已完成目标

- 视频拆解智能体生产化
- 本地视频 Agent 状态检测
- 8001 连接预检
- 视频拆解专用输入区
- 拆解模式选择
- 高级参数 workflow_options_json
- video_script_workflow steps 标准化
- 视频拆解结构化 result_json
- VideoBreakdownResultPanel
- 任务概览展示
- 执行步骤展示
- 镜头时间轴展示
- 字幕 OCR 展示
- 卖点识别展示
- 视觉证明帧展示
- 质量警告展示
- 输出文件管理
- Artifact 预览与下载
- Debug Payload 增强
- 失败提示优化
- 任务状态会话回写
- SQLite 持久化验证
## v1.5.8 已完成目标
- qa_conversation_store 增量 upsert
- conversation_store 增量 upsert
- bulk replace 仅保留给 migration
- Dataset metadata 迁入 APP SQLite
- datasets 表
- dataset_files 表
- dataset_jobs 表
- datasets.json legacy 迁移
- storage health 增加 dataset 表统计
- service_events 轻量事件钩子
- task_store 移除对 conversation_store 的函数内延迟 import
- run updated 事件同步 conversation
- 现有 API 返回结构保持不变
- 用户隔离验证
- Dataset 功能验证
## v1.5.7 已完成目标

- API.md 乱码修复
- PRD.md 乱码修复
- APP SQLite 初始化
- APP SQLite migrations
- JSON legacy backup
- JSON to SQLite migrator
- 用户账号迁移
- 审计日志迁移
- QA conversation 迁移
- agent conversation 迁移
- agent runs 迁移
- connector/debug payload/files/artifacts metadata 迁移
- SQLite storage health API
- JSON store 替换为 SQLite store
- 用户隔离验证
- 权限验证

## v1.5.6 已完成目标

- DeepSeek stream_answer
- QA stream service
- POST /api/qa/chat/stream
- SSE event 格式
- start/retrieval_start/sources/delta/done/error 事件
- 前端 ReadableStream 解析
- /chat 流式渲染
- 停止生成
- 复制回答
- 重新生成
- sources 折叠展示
- warnings/error 优化
- 流式完成后持久化 assistant message
- 流式失败后持久化 failed message
- 非流式 fallback

## v1.5.5 已完成目标

- /api/qa/model-status
- /api/qa/test-embedding
- /api/qa/test-retrieval
- /api/qa/diagnose
- qa_model_diagnostic_service
- qa_embedding_service 状态检测增强
- KnowledgeBasePanel 模型状态区
- Embedding 测试按钮
- RAG 检索测试按钮
- 知识库诊断按钮
- 诊断 checks 展示
- RAG_MODEL_SETUP.md
- 模型缺失清晰提示
- DeepSeek 未配置清晰提示
- SQLite RAG 状态展示

## 后续计划

- v1.6：视频拆解智能体生产化
- v1.7：智能体蓝图与方法论配置中心
- v1.8：参考项目拆解助手
