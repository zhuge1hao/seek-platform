"use client";

import useSWR from "swr";
import { getAgentConnectors, type AgentConnector } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useAgentConnectors(enabled = true) {
  return useSWR<{ items: AgentConnector[] }>(
    enabled ? queryKeys.agentConnectors : null,
    getAgentConnectors,
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}
