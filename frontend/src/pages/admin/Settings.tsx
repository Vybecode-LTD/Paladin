import { useEffect, useState } from "react";
import { Save, Send } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import SenderSettings from "@/components/SenderSettings";

interface SmtpSettings {
  host: string;
  port: number;
  username: string;
  password_set: boolean;
  use_tls: boolean;
  from_name: string;
  from_email: string;
  updated_at: string | null;
}

const EMPTY_FORM = {
  host: "",
  port: 587,
  username: "",
  password: "",
  use_tls: true,
  from_name: "",
  from_email: "",
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
          from_email: data.from_email,
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
        from_email: form.from_email,
      });
      setForm({
        host: data.host,
        port: data.port,
        username: data.username,
        password: "",
        use_tls: data.use_tls,
        from_name: data.from_name,
        from_email: data.from_email,
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

  const sectionTitle: React.CSSProperties = {
    fontSize: 20, fontWeight: 700, marginBottom: 6,
  };
  const sectionNote: React.CSSProperties = {
    fontSize: 14, color: "var(--text-muted)", marginBottom: 18,
    maxWidth: "70ch", lineHeight: 1.55,
  };

  return (
    <div>
      <h1 style={{ fontSize: 30, fontWeight: 800, marginBottom: 28 }}>Settings</h1>

      {/* Two mail configurations on one screen is a reasonable thing to be
          confused by, so each section says what it is for. They are separate
          because they are separate: one is a person answering a single demo
          request, the other is a campaign to a list, and they should be able
          to send from different domains with different reputations. */}
      <h2 style={sectionTitle}>Demo replies</h2>
      <p style={sectionNote}>
        The company's own mail server, used when someone answers a demo request from the
        inbox. One message at a time, to one person.
      </p>

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
              <label htmlFor="use_tls" style={{ fontSize: 14, color: "var(--text)" }}>Use STARTTLS (port 587). Port 465 always uses implicit TLS.</label>
            </div>
            <div>
              <label style={labelStyle}>From email</label>
              <input type="email" style={inputStyle} value={form.from_email}
                placeholder="info@ashfordbriggs.com"
                onChange={(e) => setForm({ ...form, from_email: e.target.value })} />
              <p style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 6 }}>
                Address demo replies are sent from. It must be one this SMTP account is
                allowed to send as, or the mail server will reject it. Leave blank to use
                info@ashfordbriggs.com.
              </p>
            </div>
            <div>
              <label style={labelStyle}>From name</label>
              <input style={inputStyle} value={form.from_name}
                onChange={(e) => setForm({ ...form, from_name: e.target.value })} />
              <p style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 6 }}>
                Display name shown alongside the sender address.
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

      <div style={{ borderTop: "1px solid var(--border)", margin: "40px 0 28px" }} />

      <h2 style={sectionTitle}>Campaign sending</h2>
      <p style={sectionNote}>
        How campaigns to a list are sent, and where their tracking and unsubscribe links
        point. Kept separate from the settings above on purpose: campaigns should send from
        their own domain, so a problem with one can never affect the other.
      </p>
      <SenderSettings />
    </div>
  );
}
