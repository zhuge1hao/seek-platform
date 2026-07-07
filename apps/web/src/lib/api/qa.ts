import { API_BASE_URL, apiFetch, parseJsonResponse } from "./core";
import type { KnowledgeChunkPreview, KnowledgeDocument, KnowledgeStats, KnowledgeUploadResponse, QAChatPayload, QAChatResponse, QAConversation, QAConversationSummary, QADiagnoseResult, QAEmbeddingTestResult, QAHealth, QAModelStatus, QARetrievalTestResult } from "./types";

export async function getQAHealth(): Promise<QAHealth> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/health`));
}

export async function getQAModelStatus(params: { include_load_check?: boolean } = {}): Promise<QAModelStatus> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/model-status?include_load_check=${Boolean(params.include_load_check)}`));
}

export async function testQAEmbedding(payload: { text: string }): Promise<QAEmbeddingTestResult> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/test-embedding`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function testQARetrieval(payload: { question: string; top_k?: number }): Promise<QARetrievalTestResult> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/test-retrieval`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function diagnoseQAKnowledge(payload: { question?: string; run_embedding_test?: boolean; run_retrieval_test?: boolean; run_deepseek_config_check?: boolean } = {}): Promise<QADiagnoseResult> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/diagnose`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function listQAConversations(limit = 50): Promise<{ conversations: QAConversationSummary[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/conversations?limit=${limit}`));
}

export async function getQAConversation(conversationId: string): Promise<{ conversation: QAConversation }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/conversations/${encodeURIComponent(conversationId)}`));
}

export async function createQAConversation(payload: { title?: string } = {}): Promise<{ conversation_id: string; title: string }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: payload.title || "New conversation" })
  }));
}

export async function archiveQAConversation(conversationId: string): Promise<{ conversation: QAConversation }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/conversations/${encodeURIComponent(conversationId)}/archive`, { method: "POST" }));
}

export async function deleteQAConversation(conversationId: string): Promise<{ conversation: QAConversation }> {
  return archiveQAConversation(conversationId);
}

export async function qaChat(payload: QAChatPayload): Promise<QAChatResponse> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }));
}

export async function getKnowledgeStats(): Promise<KnowledgeStats> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/knowledge/stats`));
}

export async function listKnowledgeDocuments(): Promise<{ documents: KnowledgeDocument[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/knowledge/documents`));
}

export async function getKnowledgeDocument(docId: string): Promise<{ document: KnowledgeDocument; chunks_preview: KnowledgeChunkPreview[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/knowledge/documents/${encodeURIComponent(docId)}`));
}

export async function uploadKnowledgeDocument(file: File, title?: string): Promise<KnowledgeUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (title?.trim()) formData.append("title", title.trim());
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/knowledge/upload`, { method: "POST", body: formData }));
}

export async function deleteKnowledgeDocument(docId: string): Promise<{ status: string; document: KnowledgeDocument }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/knowledge/documents/${encodeURIComponent(docId)}`, { method: "DELETE" }));
}

export async function reindexKnowledgeDocument(docId: string): Promise<KnowledgeUploadResponse> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/knowledge/documents/${encodeURIComponent(docId)}/reindex`, { method: "POST" }));
}
