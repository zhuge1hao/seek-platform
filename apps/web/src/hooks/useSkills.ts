"use client";

import { getSkillTemplates, type SkillTemplate } from "@/lib/api";
import { useApiQuery } from "@/hooks/useApiQuery";
import { queryKeys } from "@/lib/queryKeys";

export function useSkills(agentType?: string, enabled = true) {
  return useApiQuery<{ items: SkillTemplate[] }>(
    queryKeys.skills(agentType),
    () => getSkillTemplates(agentType),
    { enabled }
  );
}
