// API client for the Ashford & Briggs backend.
// In dev, Vite proxies /api -> http://localhost:8000 (see vite.config.ts).
const BASE = "/api";

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("ab_access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handle(res: Response) {
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  get: (path: string) =>
    fetch(`${BASE}${path}`, { headers: { ...authHeaders() } }).then(handle),

  post: (path: string, body?: unknown) =>
    fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: body ? JSON.stringify(body) : undefined,
    }).then(handle),

  patch: (path: string, body: unknown) =>
    fetch(`${BASE}${path}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(body),
    }).then(handle),

  del: (path: string) =>
    fetch(`${BASE}${path}`, {
      method: "DELETE",
      headers: { ...authHeaders() },
    }).then(handle),

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
