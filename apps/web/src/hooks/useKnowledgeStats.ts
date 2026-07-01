"use client";

import useSWR from "swr";
import { getKnowledgeStats, getQAModelStatus, listKnowledgeDocuments, type KnowledgeDocument, type KnowledgeStats, type QAModelStatus } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useKnowledgeStats(enabled = true) {
  return useSWR<KnowledgeStats>(
    enabled ? queryKeys.knowledgeStats : null,
    getKnowledgeStats,
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: enabled ? 60000 : 0 }
  );
}

export function useQAModelStatus(enabled = true, includeLoadCheck = false) {
  return useSWR<QAModelStatus>(
    enabled ? queryKeys.qaModelStatus(includeLoadCheck) : null,
    () => getQAModelStatus({ include_load_check: includeLoadCheck }),
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: enabled ? 60000 : 0 }
  );
}

export function useKnowledgeDocuments(enabled = true) {
  return useSWR<{ documents: KnowledgeDocument[] }>(
    enabled ? queryKeys.knowledgeDocuments : null,
    listKnowledgeDocuments,
    { keepPreviousData: true, revalidateOnFocus: false, refreshInterval: 0 }
  );
}
