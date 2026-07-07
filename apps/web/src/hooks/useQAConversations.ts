"use client";

import { useApiQuery } from "@/hooks/useApiQuery";
import { listQAConversations, type QAConversationSummary } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useQAConversations(limit = 50) {
  return useApiQuery<{ conversations: QAConversationSummary[] }>(
    queryKeys.qaConversations(limit),
    () => listQAConversations(limit)
  );
}
