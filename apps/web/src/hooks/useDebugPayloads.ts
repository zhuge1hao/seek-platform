"use client";

import { listDebugPayloads, type DebugPayloadSummary } from "@/lib/api";
import { useApiQuery } from "@/hooks/useApiQuery";
import { queryKeys } from "@/lib/queryKeys";

type Params = { limit?: number; agent_type?: string; status?: string };

export function useDebugPayloads(params: Params = {}, enabled = true) {
  return useApiQuery<{ items: DebugPayloadSummary[] }>(
    queryKeys.debugPayloads(params),
    () => listDebugPayloads(params),
    { enabled }
  );
}
