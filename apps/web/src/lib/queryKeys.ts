export const queryKeys = {
  currentUser: ["current-user"] as const,
  runtimeHealth: ["runtime-health"] as const,
  storageHealth: ["storage-health"] as const,
  agentConversations: (params: { limit?: number; include_archived?: boolean } = {}) => [
    "agent-conversations",
    params.limit || 50,
    Boolean(params.include_archived),
  ] as const,
  qaConversations: (limit = 50) => ["qa-conversations", limit] as const,
  knowledgeStats: ["knowledge-stats"] as const,
  qaModelStatus: (includeLoadCheck = false) => ["qa-model-status", includeLoadCheck] as const,
};
