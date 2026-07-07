import { clearAuthSession, getAuthToken } from "@/lib/authStorage";
import { API_BASE_URL, apiFetch, parseJsonResponse } from "./core";
import type { AgentRunSummaryDetail, QAChatPayload, QAStreamHandlers } from "./types";
function dispatchQAStreamEvent(eventName: string, dataText: string, handlers: QAStreamHandlers) {
  const data = dataText ? JSON.parse(dataText) : {};
  if (eventName === "start") handlers.onStart?.(data);
  if (eventName === "retrieval_start") handlers.onRetrievalStart?.(data);
  if (eventName === "sources") handlers.onSources?.(data);
  if (eventName === "delta") handlers.onDelta?.(data);
  if (eventName === "done") handlers.onDone?.(data);
  if (eventName === "error") handlers.onError?.(data);
}

function consumeQAStreamBlock(block: string, handlers: QAStreamHandlers) {
  let eventName = "message";
  const dataLines: string[] = [];
  for (const line of block.split(/\r?\n/)) {
    if (line.startsWith("event:")) eventName = line.slice(6).trim();
    if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (dataLines.length) dispatchQAStreamEvent(eventName, dataLines.join("\n"), handlers);
}

export async function streamQAChat(payload: QAChatPayload, handlers: QAStreamHandlers, signal?: AbortSignal): Promise<void> {
  if (typeof ReadableStream === "undefined") throw new Error("后台服务未连接，请确认后端服务已启动。");
  const response = await apiFetch(`${API_BASE_URL}/api/qa/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal
  });
  if (!response.ok) await parseJsonResponse(response);
  if (!response.body) throw new Error("后台服务未连接，请确认后端服务已启动。");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      if (block.trim()) consumeQAStreamBlock(block, handlers);
    }
  }
  buffer += decoder.decode();
  if (buffer.trim()) consumeQAStreamBlock(buffer, handlers);
}

export type AgentRunStreamHandlers = {
  onRunChange?: (run: AgentRunSummaryDetail) => void;
  onFallback?: (error: Error) => void;
  onConnected?: () => void;
  onTerminal?: (run: AgentRunSummaryDetail) => void;
};

const TERMINAL_RUN_STATUS = new Set(["completed", "failed", "cancelled"]);

function consumeAgentRunBlock(block: string, runId: string, handlers: AgentRunStreamHandlers): boolean {
  let eventName = "message";
  const dataLines: string[] = [];
  for (const line of block.split(/\r?\n/)) {
    if (line.startsWith("event:")) eventName = line.slice(6).trim();
    if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (eventName === "heartbeat" || !dataLines.length) return false;
  const next = JSON.parse(dataLines.join("\n")) as AgentRunSummaryDetail;
  if (next.run_id !== runId) return false;
  handlers.onRunChange?.(next);
  if (TERMINAL_RUN_STATUS.has(next.status)) {
    handlers.onTerminal?.(next);
    return true;
  }
  return false;
}

export async function streamAgentRunEvents(runId: string, handlers: AgentRunStreamHandlers, signal?: AbortSignal): Promise<void> {
  const token = getAuthToken();
  if (!token) {
    handlers.onFallback?.(new Error("missing auth token"));
    return;
  }
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent-runs/${encodeURIComponent(runId)}/events`, {
      headers: { Authorization: `Bearer ${token}` },
      signal,
    });
    if (response.status === 401 || response.status === 403) clearAuthSession();
    if (!response.ok || !response.body) throw new Error(`SSE ${response.status}`);
    handlers.onConnected?.();
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split(/\r?\n\r?\n/);
      buffer = blocks.pop() || "";
      for (const item of blocks) {
        if (item.trim() && consumeAgentRunBlock(item, runId, handlers)) return;
      }
    }
  } catch (error) {
    if ((error as Error)?.name === "AbortError") return;
    handlers.onFallback?.(error instanceof Error ? error : new Error("?????????????????"));
  }
}
