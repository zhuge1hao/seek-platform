"use client";

import { listUploadedFiles, type GenericUploadResponse } from "@/lib/api";
import { useApiQuery } from "@/hooks/useApiQuery";
import { queryKeys } from "@/lib/queryKeys";

export function useFiles(extensions = "xlsx,xls,csv", limit = 50, enabled = true) {
  return useApiQuery<{ files: GenericUploadResponse[] }>(
    queryKeys.uploadedFiles(extensions, limit),
    () => listUploadedFiles(extensions, limit),
    { enabled }
  );
}
