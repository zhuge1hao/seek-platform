import { API_BASE_URL, apiFetch, parseJsonResponse } from "./core";
import type { AdminUser, AgentRunSummary, AuditLog, DebugPayloadDetail, DebugPayloadSummary, RuntimeConfigsStatusResponse, RuntimeHealthResponse, StorageHealthResponse } from "./types";

export async function listDebugPayloads(filters: { limit?: number; agent_type?: string; status?: string } = {}): Promise<{ items: DebugPayloadSummary[] }> {
  const query = new URLSearchParams({ limit: String(filters.limit || 50) });
  if (filters.agent_type) query.set("agent_type", filters.agent_type);
  if (filters.status) query.set("status", filters.status);
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/debug-payloads?${query}`));
}

export async function getDebugPayload(runId: string): Promise<DebugPayloadDetail> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/debug-payloads/${runId}`));
}

export async function replayDebugPayload(runId: string): Promise<{ run_id: string; replay_result: unknown }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/debug-payloads/${runId}/replay`, { method: "POST" }));
}

export async function getRuntimeHealth(): Promise<RuntimeHealthResponse> {
  const response = await apiFetch(`${API_BASE_URL}/api/admin/runtime/health`);
  return parseJsonResponse<RuntimeHealthResponse>(response);
}

export async function getStorageHealth(): Promise<StorageHealthResponse> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/storage/health`));
}

export async function getRuntimeConfigsStatus(): Promise<RuntimeConfigsStatusResponse> {
  const response = await apiFetch(`${API_BASE_URL}/api/admin/runtime/configs/status`);
  return parseJsonResponse<RuntimeConfigsStatusResponse>(response);
}

export async function backupRuntimeConfigs(): Promise<Record<string, unknown>> {
  const response = await apiFetch(`${API_BASE_URL}/api/admin/runtime/configs/backup`, { method: "POST" });
  return parseJsonResponse<Record<string, unknown>>(response);
}

export async function repairRuntimeConfigs(): Promise<Record<string, unknown>> {
  const response = await apiFetch(`${API_BASE_URL}/api/admin/runtime/configs/repair`, { method: "POST" });
  return parseJsonResponse<Record<string, unknown>>(response);
}

export async function resetRuntimeConfigs(): Promise<Record<string, unknown>> {
  const response = await apiFetch(`${API_BASE_URL}/api/admin/runtime/configs/reset`, { method: "POST" });
  return parseJsonResponse<Record<string, unknown>>(response);
}

export async function clearRuntimeCache(): Promise<Record<string, unknown>> {
  const response = await apiFetch(`${API_BASE_URL}/api/admin/runtime/cache/clear`, { method: "POST" });
  return parseJsonResponse<Record<string, unknown>>(response);
}

export async function getAuditLogs(filters: { action?: string; user?: string; status?: string; start_time?: string; end_time?: string; limit?: number } = {}): Promise<{ logs: AuditLog[] }> {
  const query = new URLSearchParams();
  if (filters.action) query.set("action", filters.action);
  if (filters.status) query.set("status", filters.status);
  if (filters.user) query.set("user", filters.user);
  if (filters.start_time) query.set("start_time", filters.start_time);
  if (filters.end_time) query.set("end_time", filters.end_time);
  query.set("limit", String(filters.limit || 100));
  const response = await apiFetch(`${API_BASE_URL}/api/admin/audit-logs?${query.toString()}`);
  return parseJsonResponse<{ logs: AuditLog[] }>(response);
}

export async function exportAuditLogs(format: "csv" | "jsonl", filters: { action?: string; user?: string; status?: string } = {}): Promise<void> {
  const query = new URLSearchParams({ format, limit: "500" });
  if (filters.action) query.set("action", filters.action);
  if (filters.user) query.set("user", filters.user);
  if (filters.status) query.set("status", filters.status);
  const response = await apiFetch(`${API_BASE_URL}/api/admin/audit-logs/export?${query}`);
  if (!response.ok) await parseJsonResponse(response);
  const objectUrl = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = objectUrl; anchor.download = `audit_logs.${format}`; document.body.appendChild(anchor); anchor.click(); anchor.remove(); URL.revokeObjectURL(objectUrl);
}

export async function getAdminUsers(filters: { role?: string; enabled?: string; keyword?: string; limit?: number } = {}): Promise<{ users: AdminUser[] }> {
  const query = new URLSearchParams({ limit: String(filters.limit || 100) });
  if (filters.role) query.set("role", filters.role);
  if (filters.enabled) query.set("enabled", filters.enabled);
  if (filters.keyword) query.set("keyword", filters.keyword);
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/users?${query}`));
}

export async function createAdminUser(payload: { username: string; password: string; role: string; enabled: boolean; remark: string }): Promise<AdminUser> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/users`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function updateAdminUser(userId: string, payload: Partial<Pick<AdminUser, "role" | "enabled" | "remark">>): Promise<AdminUser> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/users/${userId}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function setAdminUserEnabled(userId: string, enabled: boolean): Promise<AdminUser> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/users/${userId}/${enabled ? "enable" : "disable"}`, { method: "POST" }));
}

export async function resetAdminUserPassword(userId: string, newPassword: string): Promise<{ status: string; message: string }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/users/${userId}/reset-password`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ new_password: newPassword }) }));
}

export async function getAdminUserRuns(userId: string, filters: { status?: string; agent_type?: string; limit?: number } = {}): Promise<{ runs: AgentRunSummary[] }> {
  const query = new URLSearchParams({ limit: String(filters.limit || 50) });
  if (filters.status) query.set("status", filters.status);
  if (filters.agent_type) query.set("agent_type", filters.agent_type);
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/users/${userId}/agent-runs?${query}`));
}
