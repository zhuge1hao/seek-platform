export const navigationItems = [
  { id: "chat", label: "AI对话", path: "/chat", enabled: true },
  { id: "agent", label: "AI智能体", path: "/agent", enabled: true },
  { id: "ai-creation", label: "AI创作", path: "/ai-creation", enabled: true },
  { id: "board", label: "无限画板", path: "/board", enabled: true },
  { id: "competition-diagnosis", label: "竞品分析", path: "/competition-diagnosis", enabled: true },
  { id: "bi", label: "美宅BI", path: "", enabled: false },
  { id: "shrimp", label: "万能美虾", path: "", enabled: false }
] as const;

export type NavigationItemId = (typeof navigationItems)[number]["id"];
