"use client";

import useSWR from "swr";
import { listQAConversations, type QAConversationSummary } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useQAConversations(limit = 50) {
  return useSWR<{ conversations: QAConversationSummary[] }>(
    queryKeys.qaConversations(limit),
    () => listQAConversations(limit),
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}
