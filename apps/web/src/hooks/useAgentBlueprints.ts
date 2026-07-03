"use client";

import useSWR from "swr";
import { getAgentBlueprint, listAgentBlueprints, type AgentBlueprint, type AgentBlueprintDetail } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useAgentBlueprints(enabled = true) {
  return useSWR<{ items: AgentBlueprint[] }>(
    enabled ? queryKeys.agentBlueprints : null,
    listAgentBlueprints,
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}

export function useAgentBlueprint(blueprintId?: string | null) {
  return useSWR<AgentBlueprintDetail>(
    blueprintId ? queryKeys.agentBlueprint(blueprintId) : null,
    () => getAgentBlueprint(String(blueprintId)),
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}
