// API client — single place for base URL, auth token handling, and error mapping.
// Backend is DRF + SimpleJWT. Token stored exactly as backend expects (Bearer access token).

const BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
// Default to same-origin /api (Vite proxies /api -> localhost:8000 in dev).
const API_ROOT = BASE ? `${BASE}/api` : "/api";

const ACCESS_KEY = "tmle.access";
const REFRESH_KEY = "tmle.refresh";

export function getAccess() {
  return localStorage.getItem(ACCESS_KEY);
}
export function getRefresh() {
  return localStorage.getItem(REFRESH_KEY);
}
export function setTokens({ access, refresh }) {
  if (access) localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}
export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function apiRoot() {
  return API_ROOT;
}

async function tryRefresh() {
  const refresh = getRefresh();
  if (!refresh) {
    clearTokens();
    window.dispatchEvent(new Event("auth-expired"));
    return null;
  }
  try {
    const res = await fetch(`${API_ROOT}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) {
      clearTokens();
      window.dispatchEvent(new Event("auth-expired"));
      return null;
    }
    const data = await res.json();
    if (data.access) {
      localStorage.setItem(ACCESS_KEY, data.access);
      if (data.refresh) localStorage.setItem(REFRESH_KEY, data.refresh);
      return data.access;
    }
    clearTokens();
    window.dispatchEvent(new Event("auth-expired"));
    return null;
  } catch {
    clearTokens();
    window.dispatchEvent(new Event("auth-expired"));
    return null;
  }
}

// statusClass maps HTTP status to UI state per spec:
// 401 -> expired/login, 403 -> no access, 404 -> not found.
export function statusKind(status) {
  if (status === 401) return "unauthorized";
  if (status === 403) return "forbidden";
  if (status === 404) return "notfound";
  if (status >= 500) return "server";
  return "error";
}

export async function apiFetch(path, { method = "GET", body, auth = true, retry = true } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getAccess();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }
  let res;
  try {
    res = await fetch(`${API_ROOT}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (e) {
    const err = new Error("Network error — is the backend running?");
    err.kind = "network";
    err.status = 0;
    throw err;
  }
  if (res.status === 401 && auth && retry) {
    const next = await tryRefresh();
    if (next) {
      return apiFetch(path, { method, body, auth, retry: false });
    }
    const err = new Error("Session expired — please log in again.");
    err.kind = "unauthorized";
    err.status = 401;
    throw err;
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (typeof data === "string") detail = data;
      else if (data.detail) detail = Array.isArray(data.detail) ? data.detail.join(" ") : String(data.detail);
      else {
        // DRF field errors: flatten first message(s)
        const parts = [];
        for (const [k, v] of Object.entries(data)) {
          parts.push(`${k}: ${Array.isArray(v) ? v.join(" ") : v}`);
        }
        if (parts.length) detail = parts.join(" | ");
      }
    } catch {
      try {
        const t = await res.text();
        if (t) detail = t.slice(0, 300);
      } catch {
        /* ignore */
      }
    }
    const kind =
      res.status === 401
        ? "unauthorized"
        : res.status === 403
          ? "forbidden"
          : res.status === 404
            ? "notfound"
            : "error";
    const friendly =
      res.status === 403
        ? `No access — ${detail}`
        : res.status === 404
          ? `Not found — ${detail}`
          : detail;
    const err = new Error(friendly);
    err.kind = kind;
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) return null;
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

// ---- Endpoint wrappers (real backend routes) ----
export const AuthAPI = {
  login: (username, password) =>
    apiFetch("/auth/token/", { method: "POST", body: { username, password }, auth: false }),
  me: () => apiFetch("/auth/me/"),
  register: (payload) =>
    apiFetch("/auth/register/", { method: "POST", body: payload, auth: false }),
  applyTenant: (payload) =>
    apiFetch("/auth/tenant-application/", { method: "POST", body: payload, auth: false }),
  applicationStatus: (payload) =>
    apiFetch("/auth/application-status/", { method: "POST", body: payload, auth: false }),
  changePassword: (payload) =>
    apiFetch("/auth/change-password/", { method: "POST", body: payload }),
};

export const UsersAPI = {
  list: () => apiFetch("/auth/users/"),
  get: (id) => apiFetch(`/auth/users/${id}/`),
  create: (payload) => apiFetch("/auth/users/", { method: "POST", body: payload }),
  update: (id, payload) => apiFetch(`/auth/users/${id}/`, { method: "PATCH", body: payload }),
  remove: (id) => apiFetch(`/auth/users/${id}/`, { method: "DELETE" }),
};

export const TenantsAPI = {
  list: () => apiFetch("/tenants/"),
  publicList: () => apiFetch("/tenants/public/", { auth: false }),
  get: (id) => apiFetch(`/tenants/${id}/`),
  create: (payload) => apiFetch("/tenants/", { method: "POST", body: payload }),
  update: (id, payload) => apiFetch(`/tenants/${id}/`, { method: "PATCH", body: payload }),
  approve: (id) => apiFetch(`/tenants/${id}/approve/`, { method: "POST" }),
  reject: (id) => apiFetch(`/tenants/${id}/reject/`, { method: "POST" }),
};

export const CoursesAPI = {
  list: () => apiFetch("/courses/"),
  get: (id) => apiFetch(`/courses/${id}/`),
  create: (payload) => apiFetch("/courses/", { method: "POST", body: payload }),
  update: (id, payload) => apiFetch(`/courses/${id}/`, { method: "PATCH", body: payload }),
  remove: (id) => apiFetch(`/courses/${id}/`, { method: "DELETE" }),
};

export const AssignmentsAPI = {
  list: () => apiFetch("/assignments/"),
  get: (id) => apiFetch(`/assignments/${id}/`),
  create: (payload) => apiFetch("/assignments/", { method: "POST", body: payload }),
  remove: (id) => apiFetch(`/assignments/${id}/`, { method: "DELETE" }),
};

export const ProgressAPI = {
  list: () => apiFetch("/progress/"),
  get: (id) => apiFetch(`/progress/${id}/`),
  // Backend: only PATCH/PUT allowed for tenant users; POST returns 405.
  update: (id, progress_percentage) =>
    apiFetch(`/progress/${id}/`, { method: "PATCH", body: { progress_percentage } }),
};
