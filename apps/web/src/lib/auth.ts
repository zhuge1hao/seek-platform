const AUTH_TOKEN_KEY = "meizhaiseek_auth_token";
const AUTH_USER_KEY = "meizhaiseek_user";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type AuthUser = {
  user_id: string;
  username: string;
  role: "admin" | "operator" | "viewer" | string;
  enabled?: boolean;
};

export type LoginResponse = {
  token: string;
  token_type: string;
  expires_at: string;
  user: AuthUser;
};

function messageFrom(data: unknown, fallback: string): string {
  if (data && typeof data === "object") {
    const detail = (data as { detail?: unknown; message?: unknown }).detail ?? (data as { message?: unknown }).message;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

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

export function isAuthenticated(): boolean {
  return Boolean(getAuthToken());
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
  } catch {
    throw new Error("后台服务未连接，请确认后端服务已启动。");
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(messageFrom(data, response.status === 401 ? "账号或密码错误。" : "登录失败。"));
  const result = data as LoginResponse;
  saveAuthSession(result.token, result.user);
  return result;
}

export async function verifyAuth(): Promise<AuthUser> {
  const token = getAuthToken();
  if (!token) throw new Error("未登录");
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` } });
  } catch {
    throw new Error("后台服务未连接，请确认后端服务已启动。");
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 || response.status === 403) clearAuthSession();
    throw new Error(messageFrom(data, "登录状态无效。"));
  }
  const user = data as AuthUser;
  window.localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  return user;
}

export async function logout(): Promise<void> {
  const token = getAuthToken();
  try {
    if (token) await fetch(`${API_BASE_URL}/api/auth/logout`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
  } finally {
    clearAuthSession();
  }
}
