---
name: keyword-insight
description: 分析电商关键词 Excel 或结构化行数据，输出行业必争词、供给不足蓝海词和小众高意向蓝海词；适用于搜索投放、商品 SEO、新品企划和内容选题。
---

# 关键词洞察

使用项目现有 `keyword_insight` Agent 和 `keyword_insight_workflow`。输入必须包含标准中文字段；缺失关键字段时直接报告，不补零。

## 输入

- Excel：默认读取 `全部搜索词`。
- JSON：调用 `keyword_insight_service.analyze_rows(rows, business_context, options)`。
- `business_context` 支持行业、品类、品牌、产品、人群、材质、功能、风格、价格带和核心卖点。

## 处理约束

- 保留搜索人气、点击率和支付转化率原文；内部同时解析数值特征。
- 从“较平均值”的绝对差反推行业参考点，并返回支持行数、误差和置信度。
- 分类使用 `services/keyword_insight_rules.json` 的可解释规则，不使用关键词答案表。
- 意图标签采用基础词典和规则；LLM 语义分类仅作为未来可选增强，不影响确定性默认路径。
- 意图去重默认关闭，因为当前样本没有充分证据证明策略表只保留每簇一个词；可通过 `deduplicate_intents=true` 开启。

## 输出

返回结构化 JSON，并默认导出四个兼容工作表。详细分数、原因、置信度、意图标签和意图簇只在 JSON 中返回；仅在 `include_explanation_sheet=true` 时增加说明表。

规则依据和限制见 `docs/skills/keyword_insight_distillation.md`，操作说明见 `docs/skills/keyword_insight_usage.md`。
