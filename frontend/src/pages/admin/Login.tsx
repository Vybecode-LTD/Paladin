import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import Brandmark from "@/components/Brandmark";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      await login(email, password);
      nav("/admin");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  const inputStyle: React.CSSProperties = {
    width: "100%", padding: "12px 14px", background: "var(--bg)",
    border: "1px solid var(--border-bright)", borderRadius: "var(--radius-sm)",
    color: "var(--text)", fontSize: 15,
  };

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "var(--bg)", padding: 20 }}>
      <div className="card" style={{ width: "100%", maxWidth: 400, padding: 36 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, justifyContent: "center", marginBottom: 8 }}>
          <Brandmark size={28} />
          <span style={{ fontWeight: 700, fontSize: 18 }}>Ashford & Briggs</span>
        </div>
        <p style={{ textAlign: "center", color: "var(--text-dim)", fontSize: 14, marginBottom: 28 }}>Admin sign in</p>
        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <input style={inputStyle} type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <input style={inputStyle} type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          {error && <p style={{ color: "var(--danger)", fontSize: 14 }}>{error}</p>}
          <button type="submit" disabled={busy} className="btn btn-primary" style={{ justifyContent: "center" }}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
