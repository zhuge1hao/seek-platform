import type { AuthUser } from "@/lib/auth";
import { API_BASE_URL, apiFetch, parseJsonResponse } from "./core";

export async function getCurrentUser(): Promise<AuthUser> {
  const response = await apiFetch(`${API_BASE_URL}/api/auth/me`);
  return parseJsonResponse<AuthUser>(response);
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<{ status: string; message: string }> {
  const response = await apiFetch(`${API_BASE_URL}/api/auth/change-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
  });
  return parseJsonResponse<{ status: string; message: string }>(response);
}
