import { API_BASE_URL, apiFetch, parseJsonResponse } from "./core";
import type { AgentConnector, AgentRunCreatePayload, ConnectorTestResult, PayloadPreviewResult } from "./types";

export async function getAgentConnectors(): Promise<{ items: AgentConnector[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-connectors`));
}

export async function createAgentConnector(payload: AgentConnector): Promise<AgentConnector> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-connectors`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function updateAgentConnector(connectorId: string, payload: Partial<AgentConnector>): Promise<AgentConnector> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-connectors/${connectorId}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function disableAgentConnector(connectorId: string): Promise<AgentConnector> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-connectors/${connectorId}`, { method: "DELETE" }));
}

export async function testAgentConnector(connectorId: string, prompt = "娴嬭瘯杩炴帴"): Promise<ConnectorTestResult> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-connectors/${connectorId}/test`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt, extra_payload: {} }) }));
}

export async function previewAgentRunPayload(payload: AgentRunCreatePayload): Promise<PayloadPreviewResult> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-runs/preview-payload`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}
