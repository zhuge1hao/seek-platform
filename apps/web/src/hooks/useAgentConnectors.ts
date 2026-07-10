"use client";

import { getAgentConnectors, type AgentConnector } from "@/lib/api";
import { useApiQuery } from "@/hooks/useApiQuery";
import { queryKeys } from "@/lib/queryKeys";

export function useAgentConnectors(enabled = true) {
  return useApiQuery<{ items: AgentConnector[] }>(queryKeys.agentConnectors, getAgentConnectors, { enabled });
}
