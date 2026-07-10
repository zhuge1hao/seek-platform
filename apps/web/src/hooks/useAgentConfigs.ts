"use client";

import { getAgentConfigs, type AgentConfig } from "@/lib/api";
import { useApiQuery } from "@/hooks/useApiQuery";
import { queryKeys } from "@/lib/queryKeys";

export function useAgentConfigs(enabled = true) {
  return useApiQuery<{ items: AgentConfig[] }>(queryKeys.agentConfigs, getAgentConfigs, { enabled });
}
