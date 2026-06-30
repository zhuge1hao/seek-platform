"use client";

import useSWR from "swr";
import { getRuntimeHealth, type RuntimeHealthResponse } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useRuntimeHealth(enabled = true) {
  return useSWR<RuntimeHealthResponse>(
    enabled ? queryKeys.runtimeHealth : null,
    getRuntimeHealth,
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: enabled ? 30000 : 0 }
  );
}
