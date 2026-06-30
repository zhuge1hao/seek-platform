"use client";

import useSWR from "swr";
import { getStorageHealth, type StorageHealthResponse } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useStorageHealth(enabled = true) {
  return useSWR<StorageHealthResponse>(
    enabled ? queryKeys.storageHealth : null,
    getStorageHealth,
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: enabled ? 30000 : 0 }
  );
}
