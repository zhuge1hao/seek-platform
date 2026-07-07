"use client";

import { useApiQuery } from "@/hooks/useApiQuery";
import { listConversations, type ConversationSummary } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

type Params = { limit?: number; include_archived?: boolean };

export function useAgentConversations(params: Params = {}) {
  return useApiQuery<{ conversations: ConversationSummary[] }>(
    queryKeys.agentConversations(params),
    () => listConversations(params)
  );
}
