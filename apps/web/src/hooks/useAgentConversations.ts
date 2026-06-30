"use client";

import useSWR from "swr";
import { listConversations, type ConversationSummary } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

type Params = { limit?: number; include_archived?: boolean };

export function useAgentConversations(params: Params = {}) {
  return useSWR<{ conversations: ConversationSummary[] }>(
    queryKeys.agentConversations(params),
    () => listConversations(params),
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}
