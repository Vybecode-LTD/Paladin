import { useEffect, useState } from "react";
import { UserPlus } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

interface UserRow {
  id: string; email: string; full_name: string; role: string; is_active: boolean;
}

const inputStyle: React.CSSProperties = {
  width: "100%", padding: "11px 13px", background: "var(--bg)",
  border: "1px solid var(--border-bright)", borderRadius: "var(--radius-sm)",
  color: "var(--text)", fontSize: 15, fontFamily: "var(--font-sans)",
};
const labelStyle: React.CSSProperties = {
  fontSize: 13, color: "var(--text-muted)", display: "block", marginBottom: 6,
};

const ROLE_STYLE: Record<string, { bg: string; fg: string }> = {
  admin: { bg: "var(--glyph-coral-bg)", fg: "var(--glyph-coral)" },
  editor: { bg: "var(--glyph-violet-bg)", fg: "var(--glyph-violet)" },
  author: { bg: "var(--glyph-blue-bg)", fg: "var(--glyph-blue)" },
};

const EMPTY_FORM = { email: "", password: "", full_name: "", role: "author" };

export default function Users() {
  const { user } = useAuth();
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function load() {
    setLoading(true);
    api.get("/auth/users").then(setUsers).catch(() => {}).finally(() => setLoading(false));
  }
  useEffect(() => {
    if (user?.role === "admin") load();
  }, [user]);

  if (user?.role !== "admin") {
    return (
      <div>
        <h1 style={{ fontSize: 30, fontWeight: 800, marginBottom: 28 }}>Users</h1>
        <div className="card" style={{ padding: 32, textAlign: "center" }}>
          <p style={{ color: "var(--text-muted)" }}>Only admins can manage users.</p>
        </div>
      </div>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.post("/auth/users", form);
      setForm(EMPTY_FORM);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create user");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 30, fontWeight: 800, marginBottom: 28 }}>Users</h1>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: 24, alignItems: "start" }}>
        <form onSubmit={submit} className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>Add a user</h3>
          <div>
            <label style={labelStyle}>Email</label>
            <input required type="email" style={inputStyle} value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
          <div>
            <label style={labelStyle}>Full name</label>
            <input style={inputStyle} value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          </div>
          <div>
            <label style={labelStyle}>Password</label>
            <input required type="password" style={inputStyle} value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </div>
          <div>
            <label style={labelStyle}>Role</label>
            <select style={inputStyle} value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="author">Author</option>
              <option value="editor">Editor</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          {error && <p style={{ color: "var(--danger)", fontSize: 14 }}>{error}</p>}
          <button type="submit" disabled={saving} className="btn btn-primary" style={{ justifyContent: "center" }}>
            <UserPlus size={16} /> {saving ? "Creating…" : "Create user"}
          </button>
        </form>

        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          {loading ? (
            <p style={{ padding: 24, color: "var(--text-dim)" }}>Loading…</p>
          ) : users.length === 0 ? (
            <p style={{ padding: 24, color: "var(--text-muted)" }}>No users yet.</p>
          ) : users.map((u) => {
            const rs = ROLE_STYLE[u.role] ?? ROLE_STYLE.author;
            return (
              <div key={u.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 20px", borderBottom: "1px solid var(--border)" }}>
                <div>
                  <div style={{ fontWeight: 600 }}>{u.full_name || u.email}</div>
                  <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{u.email}</div>
                </div>
                <span style={{
                  padding: "4px 12px", borderRadius: 999, fontSize: 12, fontFamily: "var(--font-mono)",
                  textTransform: "uppercase", fontWeight: 600, background: rs.bg, color: rs.fg,
                }}>
                  {u.role}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
