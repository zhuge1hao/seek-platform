export type AgentToolId = string;

export type AgentIconName =
  | "chart"
  | "word"
  | "target"
  | "radar"
  | "flower"
  | "message"
  | "tag"
  | "scroll"
  | "image"
  | "list"
  | "crown"
  | "layout"
  | "gift"
  | "picture"
  | "bulb"
  | "send"
  | "pin"
  | "stethoscope"
  | "video"
  | "text"
  | "code"
  | "shield";

export type AgentDefinition = {
  id: AgentToolId;
  agent_type: string;
  name: string;
  category: string;
  description: string;
  cost: number;
  enabled: boolean;
  workflow: string;
  default_mode: string;
  accepted_inputs: string[];
  default_options: Record<string, unknown>;
  icon?: AgentIconName;
  blueprint_id?: string;
  blueprint_status?: string;
  blueprint_version?: number;
  blueprint_published?: boolean;
};

export const agentList: AgentDefinition[] = [
  { id: "blue-ocean", agent_type: "blue_ocean", name: "蓝海探测", category: "市场机会", description: "用于发现类目机会、蓝海词和低竞争方向", cost: 3, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel", "link"], default_options: {}, icon: "chart" },
  { id: "keyword-demand", agent_type: "keyword_demand", name: "关键词需求分析", category: "市场机会", description: "分析关键词背后的搜索需求和购买意图", cost: 3, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel", "link"], default_options: {}, icon: "word" },
  { id: "keyword-insight", agent_type: "keyword_insight", name: "关键词洞察", category: "市场机会", description: "洞察关键词竞争、趋势和内容机会", cost: 3, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel", "link"], default_options: {}, icon: "target" },
  { id: "search-main-image", agent_type: "search_main_image", name: "搜索主图分析", category: "商品视觉", description: "分析搜索场景下主图的点击吸引力", cost: 3, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "image", "link"], default_options: {}, icon: "radar" },
  { id: "review-analysis", agent_type: "review_analysis", name: "评价分析", category: "数据诊断", description: "分析评论、差评、卖点反馈和用户痛点", cost: 3, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel", "link"], default_options: {}, icon: "flower" },
  { id: "qa-analysis", agent_type: "qa_analysis", name: "问大家分析", category: "数据诊断", description: "分析问大家内容中的用户疑虑和成交阻碍", cost: 3, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel"], default_options: {}, icon: "message" },
  { id: "title-writing", agent_type: "title_writing", name: "标题制作", category: "内容生成", description: "根据商品卖点和关键词生成标题方向", cost: 2, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel"], default_options: {}, icon: "tag" },
  { id: "main-image-planning", agent_type: "main_image_planning", name: "主图策划", category: "商品视觉", description: "策划主图卖点表达、构图和文案方向", cost: 3, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "image", "link"], default_options: {}, icon: "scroll" },
  { id: "main-image-generation", agent_type: "main_image_generation", name: "主图生成", category: "商品视觉", description: "生成主图创意方案和视觉提示词", cost: 5, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "image"], default_options: {}, icon: "image" },
  { id: "detail-page-planning", agent_type: "detail_page_planning", name: "详情页策划", category: "内容生成", description: "输出详情页结构、卖点顺序和转化文案策划", cost: 4, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel", "link", "image"], default_options: {}, icon: "list" },
  { id: "brand-detail-page-planning", agent_type: "brand_detail_page_planning", name: "品牌级详情页策划", category: "内容生成", description: "结合品牌定位策划详情页内容与视觉表达", cost: 5, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel", "link", "image"], default_options: {}, icon: "crown" },
  { id: "detail-page-generation", agent_type: "detail_page_generation", name: "详情页生成", category: "内容生成", description: "生成详情页模块文案和视觉描述", cost: 5, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "image", "link"], default_options: {}, icon: "layout" },
  { id: "buyer-show-generation", agent_type: "buyer_show_generation", name: "买家秀生成", category: "内容生成", description: "生成适合商品场景的买家秀内容方案", cost: 4, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "image", "link"], default_options: {}, icon: "gift" },
  { id: "hot-main-image-breakdown", agent_type: "hot_main_image_breakdown", name: "爆款主图拆解", category: "商品视觉", description: "拆解爆款主图的视觉结构、卖点和点击要素", cost: 3, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "image", "link"], default_options: {}, icon: "picture" },
  { id: "smart-selection", agent_type: "smart_selection", name: "智能选款", category: "市场机会", description: "结合市场数据和商品特征给出选款建议", cost: 4, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel", "link"], default_options: {}, icon: "bulb" },
  { id: "competitor-analysis", agent_type: "competitor_analysis", name: "竞品分析", category: "数据诊断", description: "用于竞品表格、链接和经营数据的综合分析", cost: 4, enabled: true, workflow: "competitor_analysis_workflow", default_mode: "default", accepted_inputs: ["text", "excel", "link"], default_options: {}, icon: "target" },
  { id: "promotion-analysis", agent_type: "promotion_analysis", name: "推广分析", category: "数据诊断", description: "分析推广投产、点击、转化和预算问题", cost: 4, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel"], default_options: {}, icon: "send" },
  { id: "region-diagnosis", agent_type: "region_diagnosis", name: "地域诊断", category: "数据诊断", description: "诊断地域表现差异和机会市场", cost: 3, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel"], default_options: {}, icon: "pin" },
  { id: "crowd-diagnosis", agent_type: "crowd_diagnosis", name: "人群诊断", category: "数据诊断", description: "诊断消费人群、转化人群和潜在人群机会", cost: 3, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel"], default_options: {}, icon: "stethoscope" },
  { id: "video-script-breakdown", agent_type: "video_script_breakdown", name: "视频脚本拆解", category: "视频脚本", description: "协议化调用本地视频脚本拆解 agent，输出结构化脚本与文件结果", cost: 3, enabled: true, workflow: "video_script_workflow", default_mode: "standard_breakdown", accepted_inputs: ["text", "video", "link"], default_options: {}, icon: "video" },
  { id: "video-script-rewrite", agent_type: "video_script_rewrite", name: "视频脚本仿写", category: "视频脚本", description: "基于参考视频或文案生成可复用脚本仿写方向", cost: 4, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "video", "link"], default_options: {}, icon: "text" },
  { id: "video-script-generation", agent_type: "video_script_generation", name: "视频脚本生成", category: "视频脚本", description: "根据商品卖点和目标人群生成视频脚本", cost: 4, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel", "link"], default_options: {}, icon: "code" },
  { id: "tax-risk-diagnosis", agent_type: "tax_risk_diagnosis", name: "税务风险诊断", category: "风险诊断", description: "用于初步梳理经营数据中的税务风险提示", cost: 5, enabled: true, workflow: "generic_agent_workflow", default_mode: "default", accepted_inputs: ["text", "excel"], default_options: {}, icon: "shield" }
];

export function findAgentById(agentId: AgentToolId | null | undefined, agents: AgentDefinition[] = agentList) {
  return agents.find((agent) => agent.id === agentId);
}

export function findAgentByType(agentType: string | null | undefined, agents: AgentDefinition[] = agentList) {
  return agents.find((agent) => agent.agent_type === agentType);
}
