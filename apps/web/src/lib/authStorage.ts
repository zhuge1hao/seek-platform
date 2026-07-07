"use client";

export const AUTH_TOKEN_KEY = "meizhaiseek_auth_token";
export const AUTH_USER_KEY = "meizhaiseek_user";

export type AuthUser = {
  user_id: string;
  username: string;
  role: "admin" | "operator" | "viewer" | string;
  enabled?: boolean;
};

export function saveAuthSession(token: string, user: AuthUser) {
  window.localStorage.setItem(AUTH_TOKEN_KEY, token);
  window.localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function clearAuthSession() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  window.localStorage.removeItem(AUTH_USER_KEY);
}

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  const token = window.localStorage.getItem(AUTH_TOKEN_KEY);
  if (token && !token.includes(".")) {
    clearAuthSession();
    return null;
  }
  return token;
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(AUTH_USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    clearAuthSession();
    return null;
  }
}
