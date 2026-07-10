"use client";

import { getRuntimeHealth, type RuntimeHealthResponse } from "@/lib/api";
import { useApiQuery } from "@/hooks/useApiQuery";
import { queryKeys } from "@/lib/queryKeys";

export function useRuntimeHealth(enabled = true) {
  return useApiQuery<RuntimeHealthResponse>(
    queryKeys.runtimeHealth,
    getRuntimeHealth,
    { enabled, refreshInterval: enabled ? 30000 : 0 }
  );
}
