"use client";

import { useApiQuery } from "@/hooks/useApiQuery";
import { listDatasets, getDatasetMappingTemplates, type DatasetSummary, type MappingTemplate } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

type Params = { status?: string; limit?: number };

export function useDatasets(params: Params = {}, enabled = true) {
  return useApiQuery<{ datasets: DatasetSummary[] }>(
    queryKeys.datasets(params),
    () => listDatasets(params),
    { enabled }
  );
}

export function useDatasetMappingTemplates(enabled = true) {
  return useApiQuery<{ templates: MappingTemplate[] }>(
    queryKeys.datasetMappingTemplates,
    getDatasetMappingTemplates,
    { enabled }
  );
}
