"use client";

import useSWR from "swr";
import { getSkillTemplates, type SkillTemplate } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useSkills(agentType?: string, enabled = true) {
  return useSWR<{ items: SkillTemplate[] }>(
    enabled ? queryKeys.skills(agentType) : null,
    () => getSkillTemplates(agentType),
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}
