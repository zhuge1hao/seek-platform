"use client";

import useSWR from "swr";
import { listUploadedFiles, type GenericUploadResponse } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useFiles(extensions = "xlsx,xls,csv", limit = 50, enabled = true) {
  return useSWR<{ files: GenericUploadResponse[] }>(
    enabled ? queryKeys.uploadedFiles(extensions, limit) : null,
    () => listUploadedFiles(extensions, limit),
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}
