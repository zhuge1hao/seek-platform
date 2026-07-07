import { API_BASE_URL, apiFetch, parseJsonResponse } from "./core";
import type { Conversation, ConversationDetail, ConversationSummary } from "./types";

export async function listConversations(params: { limit?: number; include_archived?: boolean } = {}): Promise<{ conversations: ConversationSummary[] }> {
  const query = new URLSearchParams({ limit: String(params.limit || 50), include_archived: String(Boolean(params.include_archived)) });
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/conversations?${query}`));
}


export async function getConversation(conversationId: string, signal?: AbortSignal): Promise<ConversationDetail> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/conversations/${encodeURIComponent(conversationId)}`, { signal }));
}

export async function renameConversation(conversationId: string, title: string): Promise<{ conversation: Conversation }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/conversations/${encodeURIComponent(conversationId)}/rename`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title })
  }));
}

export async function archiveConversation(conversationId: string): Promise<{ conversation: Conversation }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/conversations/${encodeURIComponent(conversationId)}/archive`, { method: "POST" }));
}

export async function deleteConversation(conversationId: string): Promise<{ conversation: Conversation }> {
  return archiveConversation(conversationId);
}
