import { useEffect, useState } from "react";
import { Save, Send } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

interface SmtpSettings {
  host: string;
  port: number;
  username: string;
  password_set: boolean;
  use_tls: boolean;
  from_name: string;
  updated_at: string | null;
}

const EMPTY_FORM = {
  host: "",
  port: 587,
  username: "",
  password: "",
  use_tls: true,
  from_name: "",
};

const inputStyle: React.CSSProperties = {
  width: "100%", padding: "11px 13px", background: "var(--bg)",
  border: "1px solid var(--border-bright)", borderRadius: "var(--radius-sm)",
  color: "var(--text)", fontSize: 15, fontFamily: "var(--font-sans)",
};
const labelStyle: React.CSSProperties = {
  fontSize: 13, color: "var(--text-muted)", display: "block", marginBottom: 6,
};

export default function Settings() {
  const { user } = useAuth();
  const [form, setForm] = useState(EMPTY_FORM);
  const [passwordSet, setPasswordSet] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  const [testEmail, setTestEmail] = useState("");
  const [testing, setTesting] = useState(false);
  const [testError, setTestError] = useState("");
  const [testSuccess, setTestSuccess] = useState(false);

  useEffect(() => {
    if (user?.role !== "admin") return;
    api
      .get("/admin/settings/smtp")
      .then((data: SmtpSettings) => {
        setForm({
          host: data.host,
          port: data.port,
          username: data.username,
          password: "",
          use_tls: data.use_tls,
          from_name: data.from_name,
        });
        setPasswordSet(data.password_set);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  if (user?.role !== "admin") {
    return (
      <div>
        <h1 style={{ fontSize: 30, fontWeight: 800, marginBottom: 28 }}>Settings</h1>
        <div className="card" style={{ padding: 32, textAlign: "center" }}>
          <p style={{ color: "var(--text-muted)" }}>Only admins can manage settings.</p>
        </div>
      </div>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSaved(false);
    try {
      const data: SmtpSettings = await api.put("/admin/settings/smtp", {
        host: form.host,
        port: form.port,
        username: form.username,
        password: form.password ? form.password : null,
        use_tls: form.use_tls,
        from_name: form.from_name,
      });
      setForm({
        host: data.host,
        port: data.port,
        username: data.username,
        password: "",
        use_tls: data.use_tls,
        from_name: data.from_name,
      });
      setPasswordSet(data.password_set);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  async function sendTest(e: React.FormEvent) {
    e.preventDefault();
    setTesting(true);
    setTestError("");
    setTestSuccess(false);
    try {
      await api.post("/admin/settings/smtp/test", { to_email: testEmail });
      setTestSuccess(true);
    } catch (err) {
      setTestError(err instanceof Error ? err.message : "Failed to send test email");
    } finally {
      setTesting(false);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 30, fontWeight: 800, marginBottom: 28 }}>Settings</h1>
      {loading ? (
        <p style={{ color: "var(--text-dim)" }}>Loading…</p>
      ) : (
        <div className="admin-grid-2col" style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 24, alignItems: "start" }}>
          <form onSubmit={submit} className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700 }}>SMTP settings</h3>
            <div>
              <label style={labelStyle}>Host</label>
              <input required style={inputStyle} value={form.host}
                onChange={(e) => setForm({ ...form, host: e.target.value })} />
            </div>
            <div>
              <label style={labelStyle}>Port</label>
              <input required type="number" style={inputStyle} value={form.port}
                onChange={(e) => setForm({ ...form, port: Number(e.target.value) })} />
            </div>
            <div>
              <label style={labelStyle}>Username</label>
              <input style={inputStyle} value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })} />
            </div>
            <div>
              <label style={labelStyle}>Password</label>
              <input
                type="password"
                style={inputStyle}
                value={form.password}
                placeholder={passwordSet ? "Leave blank to keep existing password" : ""}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
              {passwordSet && (
                <p style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 6 }}>
                  A password is already saved — leave blank to keep it.
                </p>
              )}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                id="use_tls"
                type="checkbox"
                checked={form.use_tls}
                onChange={(e) => setForm({ ...form, use_tls: e.target.checked })}
              />
              <label htmlFor="use_tls" style={{ fontSize: 14, color: "var(--text)" }}>Use TLS</label>
            </div>
            <div>
              <label style={labelStyle}>From name</label>
              <input style={inputStyle} value={form.from_name}
                onChange={(e) => setForm({ ...form, from_name: e.target.value })} />
              <p style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 6 }}>
                Display name shown alongside the fixed sender address info@ashfordbriggs.com.
              </p>
            </div>
            {error && <p style={{ color: "var(--danger)", fontSize: 14 }}>{error}</p>}
            {saved && !error && <p style={{ color: "var(--success)", fontSize: 14 }}>Settings saved.</p>}
            <button type="submit" disabled={saving} className="btn btn-primary" style={{ justifyContent: "center" }}>
              <Save size={16} /> {saving ? "Saving…" : "Save settings"}
            </button>
          </form>

          <form onSubmit={sendTest} className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700 }}>Send test email</h3>
            <div>
              <label style={labelStyle}>Send to</label>
              <input required type="email" style={inputStyle} value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)} />
            </div>
            {testError && <p style={{ color: "var(--danger)", fontSize: 14 }}>{testError}</p>}
            {testSuccess && !testError && <p style={{ color: "var(--success)", fontSize: 14 }}>Test email sent.</p>}
            <button type="submit" disabled={testing || !testEmail} className="btn btn-ghost" style={{ justifyContent: "center" }}>
              <Send size={16} /> {testing ? "Sending…" : "Send test email"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
