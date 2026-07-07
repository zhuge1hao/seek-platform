import { clearAuthSession, getAuthToken } from "@/lib/authStorage";
import { markPerf } from "@/lib/perf";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getAuthToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  try {
    const response = await globalThis.fetch(input, { ...init, headers });
    if (response.status === 401) {
      clearAuthSession();
      if (typeof window !== "undefined" && window.location.pathname !== "/login") window.location.replace("/login");
    }
    return response;
  } catch {
    throw new Error("Network request failed");
  }
}

export function parseApiError(status: number, data: unknown): string {
  const payload = data as { detail?: unknown; message?: unknown } | null;
  const message = status === 403 ? "Forbidden" : payload?.detail || payload?.message || `Request failed: ${status}`;
  return typeof message === "string" ? message : JSON.stringify(message);
}

export async function parseJsonResponse<T>(response: Response): Promise<T> {
  const end = markPerf("api.json", { status: response.status, url: response.url });
  const data = await response.json().catch(() => null);
  end();
  if (!response.ok) throw new Error(parseApiError(response.status, data));
  return data as T;
}

export function downloadArtifactUrl(downloadUrl: string): string {
  if (downloadUrl.startsWith("http://") || downloadUrl.startsWith("https://")) return downloadUrl;
  return `${API_BASE_URL}${downloadUrl.startsWith("/") ? "" : "/"}${downloadUrl}`;
}

export async function downloadArtifact(downloadUrl: string, filename = "download"): Promise<void> {
  const response = await apiFetch(downloadArtifactUrl(downloadUrl));
  if (!response.ok) await parseJsonResponse(response);
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}

export async function getArtifactBlobUrl(downloadUrl: string): Promise<string> {
  const response = await apiFetch(downloadArtifactUrl(downloadUrl));
  if (!response.ok) await parseJsonResponse(response);
  return URL.createObjectURL(await response.blob());
}
