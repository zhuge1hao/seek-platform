import { API_BASE_URL, apiFetch, parseJsonResponse } from "./core";
import type { AgentBlueprint, AgentBlueprintDetail, AgentBlueprintDiff, AgentBlueprintRegistrySyncApply, AgentBlueprintRegistrySyncPreview, AgentBlueprintReleaseGate, AgentBlueprintTestCase, AgentBlueprintTestRun, AgentBlueprintValidation, AgentBlueprintValidationRecord, AgentBlueprintVersion } from "./types";

export async function listAgentBlueprints(): Promise<{ items: AgentBlueprint[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints`));
}

export async function getAgentBlueprint(blueprintId: string): Promise<AgentBlueprintDetail> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}`));
}

export async function createAgentBlueprint(payload: Record<string, unknown>): Promise<AgentBlueprintDetail> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function updateAgentBlueprint(blueprintId: string, payload: Record<string, unknown>): Promise<AgentBlueprintDetail> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function createAgentBlueprintVersion(blueprintId: string, payload: Record<string, unknown>): Promise<{ version: AgentBlueprintVersion }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/versions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function validateAgentBlueprint(blueprintId: string): Promise<AgentBlueprintValidation> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/validate`, { method: "POST" }));
}

export async function publishAgentBlueprint(blueprintId: string, versionId?: string, confirmWarnings = false): Promise<AgentBlueprintDetail> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/publish`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ version_id: versionId, confirm_warnings: confirmWarnings }) }));
}

export async function rollbackAgentBlueprint(blueprintId: string, versionId: string): Promise<AgentBlueprintDetail> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/rollback`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ version_id: versionId }) }));
}

export async function cloneAgentBlueprint(blueprintId: string): Promise<AgentBlueprintDetail> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/clone`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) }));
}

export async function setAgentBlueprintState(blueprintId: string, action: "disable" | "enable" | "deprecate"): Promise<AgentBlueprintDetail> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/${action}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) }));
}

export async function saveAgentBlueprintTestCase(blueprintId: string, payload: Record<string, unknown>, testCaseId?: string): Promise<{ test_case: AgentBlueprintTestCase }> {
  const url = `${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/test-cases${testCaseId ? `/${encodeURIComponent(testCaseId)}` : ""}`;
  return parseJsonResponse(await apiFetch(url, { method: testCaseId ? "PATCH" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function runAgentBlueprintTestCase(blueprintId: string, testCaseId: string): Promise<Record<string, unknown>> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/test-cases/${encodeURIComponent(testCaseId)}/run`, { method: "POST" }));
}

export async function listAgentBlueprintValidations(blueprintId: string): Promise<{ items: AgentBlueprintValidationRecord[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/validations`));
}

export async function listAgentBlueprintTestRuns(blueprintId: string, limit = 20): Promise<{ items: AgentBlueprintTestRun[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/test-runs?limit=${limit}`));
}

export async function checkAgentBlueprintReleaseGate(blueprintId: string, versionId?: string): Promise<AgentBlueprintReleaseGate> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/release-gate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ version_id: versionId }) }));
}

export async function diffAgentBlueprintVersions(blueprintId: string, fromVersionId: string, toVersionId: string): Promise<AgentBlueprintDiff> {
  const query = new URLSearchParams({ from_version_id: fromVersionId, to_version_id: toVersionId });
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/versions/diff?${query.toString()}`));
}

export async function previewAgentBlueprintInput(blueprintId: string, inputSchema: Record<string, unknown>): Promise<Record<string, unknown>> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/preview/input`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ input_schema: inputSchema }) }));
}

export async function previewAgentBlueprintResult(blueprintId: string, outputSchema: Record<string, unknown>, resultUiConfig: Record<string, unknown>): Promise<Record<string, unknown>> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/preview/result`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ output_schema: outputSchema, result_ui_config: resultUiConfig }) }));
}

export async function exportAgentBlueprint(blueprintId: string): Promise<Record<string, unknown>> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/${encodeURIComponent(blueprintId)}/export`));
}

export async function previewImportAgentBlueprint(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/import/preview`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function importAgentBlueprint(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/import`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function previewAgentBlueprintRegistrySync(): Promise<AgentBlueprintRegistrySyncPreview> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/registry-sync/preview`));
}

export async function applyAgentBlueprintRegistrySync(agentIds: string[]): Promise<AgentBlueprintRegistrySyncApply> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-blueprints/registry-sync/apply`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ agent_ids: agentIds, create_as: "draft" }) }));
}
