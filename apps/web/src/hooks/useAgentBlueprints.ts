"use client";

import { useApiQuery } from "@/hooks/useApiQuery";
import { diffAgentBlueprintVersions, getAgentBlueprint, listAgentBlueprints, listAgentBlueprintTestRuns, listAgentBlueprintValidations, type AgentBlueprint, type AgentBlueprintDetail, type AgentBlueprintDiff, type AgentBlueprintTestRun, type AgentBlueprintValidationRecord } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useAgentBlueprints(enabled = true) {
  return useApiQuery<{ items: AgentBlueprint[] }>(
    queryKeys.agentBlueprints,
    listAgentBlueprints,
    { enabled }
  );
}

export function useAgentBlueprint(blueprintId?: string | null) {
  return useApiQuery<AgentBlueprintDetail>(
    blueprintId ? queryKeys.agentBlueprint(blueprintId) : [],
    () => getAgentBlueprint(String(blueprintId)),
    { enabled: Boolean(blueprintId) }
  );
}

export function useBlueprintValidations(blueprintId?: string | null) {
  return useApiQuery<{ items: AgentBlueprintValidationRecord[] }>(
    blueprintId ? queryKeys.agentBlueprintValidations(blueprintId) : [],
    () => listAgentBlueprintValidations(String(blueprintId)),
    { enabled: Boolean(blueprintId) }
  );
}

export function useBlueprintTestRuns(blueprintId?: string | null) {
  return useApiQuery<{ items: AgentBlueprintTestRun[] }>(
    blueprintId ? queryKeys.agentBlueprintTestRuns(blueprintId) : [],
    () => listAgentBlueprintTestRuns(String(blueprintId)),
    { enabled: Boolean(blueprintId) }
  );
}

export function useBlueprintDiff(blueprintId?: string | null, fromVersionId?: string | null, toVersionId?: string | null) {
  return useApiQuery<AgentBlueprintDiff>(
    blueprintId && fromVersionId && toVersionId ? queryKeys.agentBlueprintDiff(blueprintId, fromVersionId, toVersionId) : [],
    () => diffAgentBlueprintVersions(String(blueprintId), String(fromVersionId), String(toVersionId)),
    { enabled: Boolean(blueprintId && fromVersionId && toVersionId) }
  );
}
