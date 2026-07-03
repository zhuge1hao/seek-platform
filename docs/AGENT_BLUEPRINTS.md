# Agent Blueprints

## 作用

Agent Blueprint 是 v1.7 新增的智能体方法论配置中心。它统一描述智能体的基本信息、生命周期、输入协议、方法论步骤、Prompt 模板、执行绑定、输出协议、结果 UI、测试用例、验收规则、版本历史、发布、回滚、复制和导入导出。

蓝图只描述现有能力，不在 v1.7 中重写现有运行链路。

## Blueprint 与 Registry

Agent Registry 仍然是运行时智能体注册来源。没有蓝图的智能体不会消失，`/api/agents` 会返回 `blueprint_status=unmanaged`。

Blueprint 为 Registry 补充方法论、版本、输入输出、测试和发布信息。draft 或 testing 蓝图不会让未完成智能体自动变成正式可用。

## Blueprint 与 Workflow

Workflow 仍由后端代码执行，例如视频拆解继续使用 `video_script_workflow`。蓝图的 methodology steps 用于描述、校验和验收，不会动态执行任意 JSON Python，也不会允许配置任意 shell 命令。

## 生命周期状态

- `draft`: 草稿，可编辑、复制、删除未发布草稿。
- `testing`: 测试中，可运行测试用例，但不自动对普通用户开放。
- `published`: 已发布，可作为正式蓝图展示。
- `disabled`: 已停用，保留历史数据，关联智能体拒绝新任务。
- `deprecated`: 已废弃，只读保留，不允许新建任务。

已发布版本不直接覆盖。修改已发布蓝图必须创建新版本；回滚会复制目标历史发布版本为新版本并写 release 记录。

## 数据结构

APP SQLite 新增：

- `agent_blueprints`
- `agent_blueprint_versions`
- `agent_blueprint_test_cases`
- `agent_blueprint_releases`

版本内容字段使用 JSON 保存：`input_schema_json`、`methodology_json`、`prompt_config_json`、`execution_config_json`、`output_schema_json`、`result_ui_config_json`、`acceptance_rules_json`。

## 输入协议

`input_schema` 描述表单字段，支持 `text`、`textarea`、`number`、`boolean`、`select`、`multi_select`、`file`、`image`、`video`、`excel`、`word`、`local_path`、`dataset`、`knowledge_base`。

文件和本地路径字段只描述输入，不授予任意系统路径读取权限。

## 方法论步骤

`methodology.steps` 可描述步骤 ID、名称、顺序、输入输出字段、skill、Connector、超时、失败策略和验收规则。失败策略支持 `stop`、`continue`、`retry`、`skip`。

前端使用上移、下移或 JSON 编辑维护顺序，本版不引入拖拽画布。

## Prompt 版本

Prompt 配置跟随 blueprint version。发布版本不可直接编辑；改动要创建新版本。Validator 支持 `{var}` 和 `{{ var }}` 变量引用校验，未定义变量为 error，定义但未使用为 warning。

Prompt 和导入导出都不允许保存 `password`、`token`、`api_key`、`apikey`、`secret` 等敏感字段。

## 执行绑定

`execution_config.execution_type` 支持 `internal`、`http_connector`、`cli_connector`、`mock`。发布前会校验 Agent Registry、Workflow、Connector 和 renderer。Connector 不存在或停用、Workflow 不存在、未知 renderer 都会阻止发布。

CLI Connector 必须复用现有安全机制，蓝图本身不保存可执行命令模板。

## 输出协议与结果 UI

`output_schema.sections` 可描述 `summary`、`steps`、`text`、`table`、`metrics`、`timeline`、`subtitles`、`selling_points`、`images`、`proof_frames`、`warnings`、`recommendations`、`artifacts`、`raw_preview`。

`result_ui_config.renderer` 只允许平台注册值：`generic_text`、`generic_structured`、`video_breakdown`、`table_report`、`dataset_report`。未知 renderer 校验失败；未实现 renderer 可安全降级到通用结构化展示。

## 测试和发布

测试用例保存输入、期望状态、期望结果规则、期望 artifact 和最大耗时。运行测试会复用现有 Agent Run API，生成真实 `run_id`，并在 run 终态后把 PASS/FAIL、错误和摘要写回 `last_result_json`。

发布仅 admin 可执行。operator 可创建草稿、创建版本、运行测试、复制和导出。viewer 只能查看已发布蓝图和已发布版本，不能查看未发布 Prompt，也不能运行测试。

## 复制、导入和导出

导出格式包含 `format_version`、`platform`、`exported_at`、`blueprint`、`version`、`test_cases`。导出会递归脱敏敏感字段。

导入必须先 preview。正式导入默认在 `blueprint_id` 冲突时创建新 ID；也可作为目标蓝图新版本导入，但不能覆盖已发布版本。复制蓝图默认生成 draft，清空 `published_version_id`。

## 视频拆解样板

v1.7 自动幂等创建 `bp_video_script_breakdown`，绑定：

- `agent_id`: `video_script_breakdown`
- `workflow_type`: `video_script_workflow`
- `connector_id`: `video_script_agent`
- `renderer`: `video_breakdown`
- 状态：`published`

该蓝图只描述现有视频拆解链路，不修改本地 8001 Agent，不复制本地 Agent 内部 Prompt，不重写 `video_script_workflow`。

## 安全规则

- 不保存 token、password、api key、secret。
- 不允许通过蓝图执行任意 shell。
- 不允许动态执行任意 JSON Python。
- viewer 不可查看未发布 Prompt。
- 所有写操作按角色权限控制并写审计日志。
- disabled/deprecated 关联蓝图会阻止新 Agent Run。

## 常见问题

### 蓝图会替代 Agent Registry 吗？

不会。Registry 仍然决定运行时有哪些智能体，蓝图是描述、治理、测试和发布层。

### draft 蓝图会影响现有智能体运行吗？

不会。无蓝图、draft、testing 都不改变既有 Registry/Workflow 可运行性。只有 disabled 或 deprecated 的关联蓝图会拒绝新任务。

### 视频拆解是否改成动态工作流？

没有。视频拆解仍使用稳定的 `video_script_workflow`、`video_agent_payload_builder`、`video_breakdown_result_normalizer`、8001 Connector 和 `VideoBreakdownResultPanel`。
