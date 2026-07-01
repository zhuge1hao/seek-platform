"use client";

import useSWR from "swr";
import { listDebugPayloads, type DebugPayloadSummary } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

type Params = { limit?: number; agent_type?: string; status?: string };

export function useDebugPayloads(params: Params = {}, enabled = true) {
  return useSWR<{ items: DebugPayloadSummary[] }>(
    enabled ? queryKeys.debugPayloads(params) : null,
    () => listDebugPayloads(params),
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}
