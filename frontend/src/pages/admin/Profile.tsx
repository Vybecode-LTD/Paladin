import { useState } from "react";
import { KeyRound, Mail } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const inputStyle: React.CSSProperties = {
  width: "100%", padding: "11px 13px", background: "var(--bg)",
  border: "1px solid var(--border-bright)", borderRadius: "var(--radius-sm)",
  color: "var(--text)", fontSize: 15, fontFamily: "var(--font-sans)",
};
const labelStyle: React.CSSProperties = {
  fontSize: 13, color: "var(--text-muted)", display: "block", marginBottom: 6,
};

const EMPTY_EMAIL_FORM = { new_email: "", current_password: "" };
const EMPTY_PASSWORD_FORM = { current_password: "", new_password: "", confirm_password: "" };

export default function Profile() {
  const { user, refreshUser } = useAuth();

  const [emailForm, setEmailForm] = useState(EMPTY_EMAIL_FORM);
  const [emailError, setEmailError] = useState("");
  const [emailSuccess, setEmailSuccess] = useState("");

  const [passwordForm, setPasswordForm] = useState(EMPTY_PASSWORD_FORM);
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");

  const [busy, setBusy] = useState<"email" | "password" | null>(null);

  async function submitEmail(e: React.FormEvent) {
    e.preventDefault();
    setEmailError("");
    setEmailSuccess("");
    setBusy("email");
    try {
      await api.patch("/auth/me/email", emailForm);
      await refreshUser();
      setEmailForm(EMPTY_EMAIL_FORM);
      setEmailSuccess("Email updated.");
    } catch (err) {
      setEmailError(err instanceof Error ? err.message : "Failed to update email");
    } finally {
      setBusy(null);
    }
  }

  async function submitPassword(e: React.FormEvent) {
    e.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError("New password and confirmation do not match.");
      return;
    }
    setBusy("password");
    try {
      await api.patch("/auth/me/password", {
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });
      setPasswordForm(EMPTY_PASSWORD_FORM);
      setPasswordSuccess("Password updated.");
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : "Failed to update password");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 30, fontWeight: 800, marginBottom: 28 }}>My Profile</h1>
      <div className="admin-grid-2col" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, alignItems: "start" }}>
        <form onSubmit={submitEmail} className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>Change email</h3>
          <div>
            <label style={labelStyle}>Current email</label>
            <p style={{ fontSize: 15, margin: 0 }}>{user?.email}</p>
          </div>
          <div>
            <label style={labelStyle}>New email</label>
            <input required type="email" style={inputStyle} value={emailForm.new_email}
              onChange={(e) => setEmailForm({ ...emailForm, new_email: e.target.value })} />
          </div>
          <div>
            <label style={labelStyle}>Current password</label>
            <input required type="password" style={inputStyle} value={emailForm.current_password}
              onChange={(e) => setEmailForm({ ...emailForm, current_password: e.target.value })} />
          </div>
          {emailError && <p style={{ color: "var(--danger)", fontSize: 14 }}>{emailError}</p>}
          {emailSuccess && <p style={{ color: "var(--success)", fontSize: 14 }}>{emailSuccess}</p>}
          <button type="submit" disabled={busy === "email"} className="btn btn-primary" style={{ justifyContent: "center" }}>
            <Mail size={16} /> {busy === "email" ? "Saving…" : "Update email"}
          </button>
        </form>

        <form onSubmit={submitPassword} className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>Change password</h3>
          <div>
            <label style={labelStyle}>Current password</label>
            <input required type="password" style={inputStyle} value={passwordForm.current_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })} />
          </div>
          <div>
            <label style={labelStyle}>New password</label>
            <input required type="password" style={inputStyle} value={passwordForm.new_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })} />
            <p style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 6 }}>At least 8 characters.</p>
          </div>
          <div>
            <label style={labelStyle}>Confirm new password</label>
            <input required type="password" style={inputStyle} value={passwordForm.confirm_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })} />
          </div>
          {passwordError && <p style={{ color: "var(--danger)", fontSize: 14 }}>{passwordError}</p>}
          {passwordSuccess && <p style={{ color: "var(--success)", fontSize: 14 }}>{passwordSuccess}</p>}
          <button type="submit" disabled={busy === "password"} className="btn btn-primary" style={{ justifyContent: "center" }}>
            <KeyRound size={16} /> {busy === "password" ? "Saving…" : "Update password"}
          </button>
        </form>
      </div>
    </div>
  );
}
