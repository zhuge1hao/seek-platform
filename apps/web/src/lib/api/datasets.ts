import { API_BASE_URL, apiFetch, parseJsonResponse } from "./core";
import type { AgentRunFile, DatasetCleanResult, DatasetPreview, DatasetProfile, DatasetSummary, GenericUploadResponse, MappingTemplate } from "./types";

export async function createDatasetFromFile(fileId: string, name?: string): Promise<DatasetSummary & { preview: DatasetPreview; detected_fields: DatasetPreview["detected_fields"]; suggested_mapping: Record<string, string> }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/from-file`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ file_id: fileId, name: name || undefined }) }));
}

export async function listDatasets(params: { status?: string; limit?: number } = {}): Promise<{ datasets: DatasetSummary[] }> {
  const query = new URLSearchParams({ limit: String(params.limit || 50) });
  if (params.status) query.set("status", params.status);
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets?${query}`));
}

export async function getDataset(datasetId: string): Promise<DatasetSummary> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}`));
}

export async function getDatasetPreview(datasetId: string): Promise<DatasetPreview> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}/preview`));
}

export async function getDatasetMappingTemplates(): Promise<{ templates: MappingTemplate[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/mapping-templates`));
}

export async function saveDatasetFieldMapping(datasetId: string, payload: { mapping: Record<string, string>; template_name?: string; save_as_template?: boolean }): Promise<{ status: string; mapping: Record<string, string>; template?: MappingTemplate }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}/field-mapping`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function getDatasetFieldMapping(datasetId: string): Promise<{ dataset_id: string; mapping: Record<string, string>; suggested_mapping?: Record<string, string> }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}/field-mapping`));
}

export async function cleanDataset(datasetId: string, rules: Record<string, number | boolean>): Promise<DatasetCleanResult> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}/clean`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ rules }) }));
}

export async function getDatasetProfile(datasetId: string): Promise<DatasetProfile> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}/profile`));
}

export async function getDatasetFiles(datasetId: string): Promise<{ files: AgentRunFile[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}/files`));
}

export async function deleteDataset(datasetId: string): Promise<{ status: string; dataset: DatasetSummary }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}`, { method: "DELETE" }));
}
