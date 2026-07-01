"use client";

import useSWR from "swr";
import { getAgentConfigs, type AgentConfig } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useAgentConfigs(enabled = true) {
  return useSWR<{ items: AgentConfig[] }>(
    enabled ? queryKeys.agentConfigs : null,
    getAgentConfigs,
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}
