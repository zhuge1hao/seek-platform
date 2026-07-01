"use client";

import useSWR from "swr";
import { listDatasets, getDatasetMappingTemplates, type DatasetSummary, type MappingTemplate } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

type Params = { status?: string; limit?: number };

export function useDatasets(params: Params = {}, enabled = true) {
  return useSWR<{ datasets: DatasetSummary[] }>(
    enabled ? queryKeys.datasets(params) : null,
    () => listDatasets(params),
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}

export function useDatasetMappingTemplates(enabled = true) {
  return useSWR<{ templates: MappingTemplate[] }>(
    enabled ? queryKeys.datasetMappingTemplates : null,
    getDatasetMappingTemplates,
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}
