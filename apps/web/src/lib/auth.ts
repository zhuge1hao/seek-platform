import { API_BASE_URL, apiFetch, parseJsonResponse } from "@/lib/api/core";
import {
  AUTH_USER_KEY,
  clearAuthSession,
  getAuthToken,
  getStoredUser,
  saveAuthSession,
  type AuthUser
} from "@/lib/authStorage";

export { clearAuthSession, getAuthToken, getStoredUser, saveAuthSession, type AuthUser };

export type LoginResponse = {
  token: string;
  token_type: string;
  expires_at: string;
  user: AuthUser;
};

export function isAuthenticated(): boolean {
  return Boolean(getAuthToken());
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const result = await parseJsonResponse<LoginResponse>(await apiFetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  }));
  saveAuthSession(result.token, result.user);
  return result;
}

export async function verifyAuth(): Promise<AuthUser> {
  const token = getAuthToken();
  if (!token) throw new Error("Not authenticated");
  const user = await parseJsonResponse<AuthUser>(await apiFetch(`${API_BASE_URL}/api/auth/me`));
  window.localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  return user;
}

export async function logout(): Promise<void> {
  const token = getAuthToken();
  try {
    if (token) await apiFetch(`${API_BASE_URL}/api/auth/logout`, { method: "POST" });
  } finally {
    clearAuthSession();
  }
}
