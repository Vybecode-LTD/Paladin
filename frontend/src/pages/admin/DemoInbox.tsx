import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface DemoReq {
  id: string; full_name: string; company: string; email: string;
  phone: string; role: string; team_size: string; message: string;
  is_handled: boolean; created_at: string;
}

export default function DemoInbox() {
  const [rows, setRows] = useState<DemoReq[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/admin/demo-requests").then(setRows).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 style={{ fontSize: 30, fontWeight: 800, marginBottom: 28 }}>Demo Requests</h1>
      {loading ? <p style={{ color: "var(--text-dim)" }}>Loading…</p> : rows.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 40 }}>
          <p style={{ color: "var(--text-muted)" }}>No demo requests yet.</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {rows.map((r) => (
            <div key={r.id} className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                <div>
                  <h3 style={{ fontSize: 18, fontWeight: 700 }}>{r.full_name} <span style={{ color: "var(--text-dim)", fontWeight: 400 }}>· {r.company}</span></h3>
                  <div style={{ display: "flex", gap: 16, marginTop: 8, flexWrap: "wrap", fontSize: 14, color: "var(--text-muted)" }}>
                    <a href={`mailto:${r.email}`} style={{ color: "var(--accent-bright)" }}>{r.email}</a>
                    {r.phone && <span>{r.phone}</span>}
                    {r.role && <span>{r.role}</span>}
                    {r.team_size && <span>Team: {r.team_size}</span>}
                  </div>
                  {r.message && <p style={{ marginTop: 12, color: "var(--text-muted)", fontSize: 15 }}>{r.message}</p>}
                </div>
                <span style={{ fontSize: 12, color: "var(--text-dim)", fontFamily: "var(--font-mono)", whiteSpace: "nowrap" }}>
                  {new Date(r.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
