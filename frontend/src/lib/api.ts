// API client for the Ashford & Briggs backend.
// In dev, Vite proxies /api -> http://localhost:8000 (see vite.config.ts).
const BASE = "/api";

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("ab_access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// AuthContext registers this on mount so api.ts can clear `user` state when
// a refresh attempt fails, without api.ts importing React context directly.
let onAuthExpired: (() => void) | null = null;
export function setOnAuthExpired(cb: (() => void) | null) {
  onAuthExpired = cb;
}

function clearTokens() {
  localStorage.removeItem("ab_access_token");
  localStorage.removeItem("ab_refresh_token");
}

// Ensures concurrent 401s only trigger one /auth/refresh call.
let refreshPromise: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const refreshToken = localStorage.getItem("ab_refresh_token");
  if (!refreshToken) return false;

  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(`${BASE}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!res.ok) return false;
        const data = await res.json();
        localStorage.setItem("ab_access_token", data.access_token);
        localStorage.setItem("ab_refresh_token", data.refresh_token);
        return true;
      } catch {
        return false;
      }
    })().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function handle(res: Response) {
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

// Wraps a fetch-returning thunk with transparent 401 -> refresh -> retry-once.
// Returns `any` to match `handle()`'s inferred type, same as the pre-existing
// untyped api.get/post/patch/del contract every call site already relies on.
async function withAuthRetry(doFetch: () => Promise<Response>): Promise<any> {
  const res = await doFetch();
  if (res.status !== 401) return handle(res);

  const refreshed = await refreshTokens();
  if (!refreshed) {
    clearTokens();
    onAuthExpired?.();
    return handle(res);
  }
  return handle(await doFetch());
}

export const api = {
  get: (path: string) =>
    withAuthRetry(() => fetch(`${BASE}${path}`, { headers: { ...authHeaders() } })),

  post: (path: string, body?: unknown) =>
    withAuthRetry(() =>
      fetch(`${BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: body ? JSON.stringify(body) : undefined,
      })
    ),

  patch: (path: string, body: unknown) =>
    withAuthRetry(() =>
      fetch(`${BASE}${path}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(body),
      })
    ),

  del: (path: string) =>
    withAuthRetry(() =>
      fetch(`${BASE}${path}`, {
        method: "DELETE",
        headers: { ...authHeaders() },
      })
    ),

  // Login uses form-encoded body (OAuth2PasswordRequestForm on the backend).
  login: (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    return fetch(`${BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    }).then(handle);
  },
};

// NOTE ON AI CALLS:
// The admin AI-assist features call our OWN backend (/api/admin/ai/*), which
// proxies to Anthropic server-side — the API key never reaches the browser.
// This is the production-safe pattern. (If you ever build a standalone sandbox
// artifact that must call Anthropic directly, that is the separate sandbox-mode
// path with the anthropic-dangerous-direct-browser-access header — not used here
// because we have a real backend proxy.)
export const aiApi = {
  draft: (topic: string, tone: string, length: string) =>
    api.post("/admin/ai/draft", { topic, tone, length }),
  titles: (topic: string) => api.post("/admin/ai/titles", { topic }),
  excerpt: (body_markdown: string) => api.post("/admin/ai/excerpt", { body_markdown }),
  seo: (title: string, body_markdown: string) =>
    api.post("/admin/ai/seo", { title, body_markdown }),
};
