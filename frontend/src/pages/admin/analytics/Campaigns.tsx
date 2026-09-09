import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";
import { api } from "@/lib/api";
import { StatusChip } from "./parts";

interface CampaignRow {
  id: string; name: string; subject: string; status: string; segment: string;
  scheduled_for: string | null; sent_at: string | null; error: string;
  created_at: string;
}

export default function Campaigns() {
  const [rows, setRows] = useState<CampaignRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/admin/campaigns")
      .then(setRows)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18, gap: 12, flexWrap: "wrap" }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>Campaigns</h2>
        <Link to="/admin/analytics/campaigns/new" className="btn btn-primary">
          <Plus size={16} /> New campaign
        </Link>
      </div>

      {loading ? (
        <p style={{ color: "var(--text-dim)" }}>Loading…</p>
      ) : rows.length === 0 ? (
        <div className="card" style={{ padding: 32, textAlign: "center" }}>
          <p style={{ color: "var(--text-muted)", margin: 0 }}>No campaigns yet.</p>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: "14px 20px" }}>
                    <Link
                      to={
                        // A draft has no numbers to show yet, so it opens in
                        // the editor; anything sent opens on its scorecard.
                        c.status === "draft"
                          ? `/admin/analytics/campaigns/${c.id}/edit`
                          : `/admin/analytics/campaigns/${c.id}`
                      }
                      style={{ fontWeight: 600, color: "var(--text)" }}
                    >
                      {c.name}
                    </Link>
                    <div style={{ fontSize: 12.5, color: "var(--text-dim)", marginTop: 3 }}>
                      {c.subject || "no subject yet"}
                    </div>
                    {c.error && (
                      <div style={{ fontSize: 12.5, color: "var(--warning)", marginTop: 4 }}>{c.error}</div>
                    )}
                  </td>
                  <td style={{ padding: "14px 20px", width: 140, fontSize: 13, color: "var(--text-muted)" }}>
                    {c.segment || "everyone"}
                  </td>
                  <td style={{ padding: "14px 20px", width: 120 }}>
                    <StatusChip status={c.status} />
                  </td>
                  <td style={{ padding: "14px 20px", width: 150, fontSize: 13, color: "var(--text-muted)" }}>
                    {c.sent_at
                      ? new Date(c.sent_at).toLocaleDateString()
                      : c.scheduled_for
                        ? `for ${new Date(c.scheduled_for).toLocaleDateString()}`
                        : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
