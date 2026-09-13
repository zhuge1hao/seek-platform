# 关键词洞察 Skill 使用说明

## 一、功能简述

关键词洞察从搜索词市场数据中识别行业必争搜索词、供给不足蓝海词和小众高意向蓝海词，并保留每个判断的得分、原因、置信度、意图标签和意图簇。

## 二、适用场景

适用于搜索投放、商品标题与 SEO、新品企划、市场研究、内容选题和竞品关键词分析。

## 三、输入数据

支持上传 Excel，或调用 `keyword_insight_service.analyze_rows` 传入结构化 JSON 行。关键字段为：搜索词、近7天/30天搜索人气、近7天/30天点击率、点击率较平均值、近7天/30天支付转化率、转化率较平均值。序号可省略。30 天字段可为空；关键字段列名不能缺失。

业务上下文支持 `industry`、`category`、`brand`、`product`、`target_audience`、`materials`、`functions`、`styles`、`price_segment`、`core_selling_points`。行业必争词需要业务上下文才能可靠判断。

## 四、操作步骤

1. 在平台进入“关键词洞察”。
2. 上传关键词 Excel。
3. 在 workflow options 中填写业务上下文；至少填写行业和品类，建议补充人群、材质与功能。
4. 执行分析。
5. 查看三类策略词及汇总数量。
6. 下载 JSON 或四工作表 Excel。
7. 将策略词用于投放、标题、SEO、新品和内容规划。

## 五、结果解释

- 行业必争搜索词：与业务核心方向相关，近期需求增强，点击和支付转化健康，值得优先覆盖。
- 供给不足蓝海词：已有一定搜索需求，但点击或支付转化明显偏弱，可能存在供给表达、商品匹配或承接不足。
- 小众高意向蓝海词：搜索规模较小，但点击与支付转化健康，适合精细化布局。

## 六、注意事项

1. 搜索热度高不代表一定值得投放。
2. 点击率低可能是供给问题，也可能是搜索意图不匹配。
3. 高转化低搜索词适合精细化布局。
4. 行业必争词必须结合自身产品。
5. 品牌词需要区分自有品牌与竞品品牌。
6. 一个样本无法 100% 恢复原 Skill 私有算法。
7. 本 Skill 使用可解释规则和可配置权重。
8. 平台数据更新后应重新计算行业基准。

## 七、输入示例

```json
{
  "source_file": "keywords.xlsx",
  "business_context": {
    "industry": "女性内衣",
    "category": "女士内裤",
    "target_audience": ["30-45岁女性", "45-65岁女性"],
    "materials": ["纯棉", "桑蚕丝", "羊绒"],
    "functions": ["高腰", "收腹", "无痕", "抗菌"]
  },
  "options": {
    "deduplicate_intents": false,
    "include_explanation_sheet": false
  }
}
```

## 八、输出示例

```json
{
  "summary": {"total_keywords": 300, "must_win_count": 4, "supply_gap_count": 35, "high_intent_count": 62},
  "benchmarks": {"ctr": {"value": 102.4, "status": "inferred"}, "conversion": {"value": 22.5, "status": "inferred"}},
  "must_win_keywords": [],
  "supply_gap_keywords": [],
  "high_intent_keywords": [],
  "all_keywords": []
}
```

## 九、常见问题

**为什么没有行业必争词？** 检查业务上下文是否填写，以及近期需求、30 天点击和转化是否同时满足规则。

**为什么策略数量与参考样本不同？** 当前规则来自一个样本的黑盒蒸馏，会保留无法解释的差异，不使用关键词答案表强行匹配。

**为什么 Excel 没有解释列？** 默认保持参考文件的 10 列兼容格式。JSON 包含解释；设置 `include_explanation_sheet=true` 可增加说明表。
