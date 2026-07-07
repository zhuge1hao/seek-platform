import { API_BASE_URL, apiFetch, parseJsonResponse, downloadArtifact, downloadArtifactUrl, getArtifactBlobUrl } from "./core";
import type { FilePreviewResponse, GenericUploadResponse, VideoUploadResponse } from "./types";

export async function uploadVideo(file: File): Promise<VideoUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiFetch(`${API_BASE_URL}/api/files/video/upload`, { method: "POST", body: formData });
  return parseJsonResponse<VideoUploadResponse>(response);
}

export async function uploadGenericFile(file: File): Promise<GenericUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiFetch(`${API_BASE_URL}/api/files/upload`, { method: "POST", body: formData });
  return parseJsonResponse<GenericUploadResponse>(response);
}

export async function getFilePreview(fileId: string): Promise<FilePreviewResponse> {
  const response = await apiFetch(`${API_BASE_URL}/api/files/${fileId}/preview`);
  return parseJsonResponse<FilePreviewResponse>(response);
}

export async function listUploadedFiles(extensions = "xlsx,xls,csv", limit = 50): Promise<{ files: GenericUploadResponse[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/files?extensions=${encodeURIComponent(extensions)}&limit=${limit}`));
}

export { downloadArtifact, downloadArtifactUrl, getArtifactBlobUrl };
