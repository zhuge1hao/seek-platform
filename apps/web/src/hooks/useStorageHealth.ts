"use client";

import { getStorageHealth, type StorageHealthResponse } from "@/lib/api";
import { useApiQuery } from "@/hooks/useApiQuery";
import { queryKeys } from "@/lib/queryKeys";

export function useStorageHealth(enabled = true) {
  return useApiQuery<StorageHealthResponse>(
    queryKeys.storageHealth,
    getStorageHealth,
    { enabled, refreshInterval: enabled ? 30000 : 0 }
  );
}
