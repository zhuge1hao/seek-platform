import { API_BASE_URL, apiFetch, parseJsonResponse } from "./core";
import type { AgentRunCreatePayload, AgentRunCreateResponse, AgentRunResultDetail, AgentRunStatus, AgentRunSummary, AgentRunSummaryDetail } from "./types";

export async function createAgentRun(payload: AgentRunCreatePayload): Promise<AgentRunCreateResponse> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return parseJsonResponse<AgentRunCreateResponse>(response);
}

export async function getAgentRun(runId: string, signal?: AbortSignal): Promise<AgentRunStatus> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs/${runId}`, { signal });
  return parseJsonResponse<AgentRunStatus>(response);
}

export async function getAgentRunSummary(runId: string, signal?: AbortSignal): Promise<AgentRunSummaryDetail> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs/${runId}/summary`, { signal });
  return parseJsonResponse<AgentRunSummaryDetail>(response);
}

export async function getAgentRunResult(runId: string, signal?: AbortSignal): Promise<AgentRunResultDetail> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs/${runId}/result`, { signal });
  return parseJsonResponse<AgentRunResultDetail>(response);
}

export async function cancelAgentRun(runId: string): Promise<AgentRunStatus> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs/${runId}/cancel`, { method: "POST" });
  return parseJsonResponse<AgentRunStatus>(response);
}

export async function retryAgentRun(runId: string): Promise<AgentRunCreateResponse> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs/${runId}/retry`, { method: "POST" });
  return parseJsonResponse<AgentRunCreateResponse>(response);
}

export async function listAgentRuns(limit = 20): Promise<{ items: AgentRunSummary[] }> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs?limit=${limit}`);
  return parseJsonResponse<{ items: AgentRunSummary[] }>(response);
}
