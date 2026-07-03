"use client";

import useSWR from "swr";
import { diffAgentBlueprintVersions, getAgentBlueprint, listAgentBlueprints, listAgentBlueprintTestRuns, listAgentBlueprintValidations, type AgentBlueprint, type AgentBlueprintDetail, type AgentBlueprintDiff, type AgentBlueprintTestRun, type AgentBlueprintValidationRecord } from "@/lib/api";
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

export function useBlueprintValidations(blueprintId?: string | null) {
  return useSWR<{ items: AgentBlueprintValidationRecord[] }>(
    blueprintId ? queryKeys.agentBlueprintValidations(blueprintId) : null,
    () => listAgentBlueprintValidations(String(blueprintId)),
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}

export function useBlueprintTestRuns(blueprintId?: string | null) {
  return useSWR<{ items: AgentBlueprintTestRun[] }>(
    blueprintId ? queryKeys.agentBlueprintTestRuns(blueprintId) : null,
    () => listAgentBlueprintTestRuns(String(blueprintId)),
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}

export function useBlueprintDiff(blueprintId?: string | null, fromVersionId?: string | null, toVersionId?: string | null) {
  return useSWR<AgentBlueprintDiff>(
    blueprintId && fromVersionId && toVersionId ? queryKeys.agentBlueprintDiff(blueprintId, fromVersionId, toVersionId) : null,
    () => diffAgentBlueprintVersions(String(blueprintId), String(fromVersionId), String(toVersionId)),
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}
