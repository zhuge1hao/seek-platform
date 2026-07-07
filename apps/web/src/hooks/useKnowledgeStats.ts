"use client";

import { useApiQuery } from "@/hooks/useApiQuery";
import { getKnowledgeStats, getQAModelStatus, listKnowledgeDocuments, type KnowledgeDocument, type KnowledgeStats, type QAModelStatus } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useKnowledgeStats(enabled = true) {
  return useApiQuery<KnowledgeStats>(
    queryKeys.knowledgeStats,
    getKnowledgeStats,
    { enabled, refreshInterval: enabled ? 60000 : 0 }
  );
}

export function useQAModelStatus(enabled = true, includeLoadCheck = false) {
  return useApiQuery<QAModelStatus>(
    queryKeys.qaModelStatus(includeLoadCheck),
    () => getQAModelStatus({ include_load_check: includeLoadCheck }),
    { enabled, refreshInterval: enabled ? 60000 : 0 }
  );
}

export function useKnowledgeDocuments(enabled = true) {
  return useApiQuery<{ documents: KnowledgeDocument[] }>(
    queryKeys.knowledgeDocuments,
    listKnowledgeDocuments,
    { enabled }
  );
}
