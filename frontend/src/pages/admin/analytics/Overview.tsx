import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { Stat, StatRow, StatusChip } from "./parts";

interface RecentCampaign {
  id: string; name: string; status: string; segment: string;
  sent_at: string | null; created_at: string;
}

interface OverviewData {
  campaigns_total: number;
  campaigns_sent: number;
  messages: number;
  sent: number;
  verified_engagement: number;
  complaints: number;
  complaint_rate: number | null;
  recent: RecentCampaign[];
}

interface SendTime {
  enough_data: boolean;
  observations: number;
  needed?: number;
  note?: string;
  best_hour_utc?: number;
  best_weekday?: string;
}

/** Complaint rate is the number that gets a domain blocked: providers act at
 * 0.3% and prefer under 0.1%. It belongs on the front page rather than buried
 * in a screen nobody opens. */
function complaintTone(rate: number | null): "good" | "warn" | "bad" | undefined {
  if (rate === null) return undefined;
  if (rate >= 0.003) return "bad";
  if (rate >= 0.001) return "warn";
  return "good";
}

export default function Overview() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [sendTime, setSendTime] = useState<SendTime | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/admin/analytics/overview"),
      api.get("/admin/analytics/send-time"),
    ])
      .then(([o, s]) => { setData(o); setSendTime(s); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ color: "var(--text-dim)" }}>Loading…</p>;
  if (!data) return <p style={{ color: "var(--danger)" }}>Could not load analytics.</p>;

  if (data.campaigns_total === 0) {
    return (
      <div className="card" style={{ padding: 36, textAlign: "center" }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>No campaigns yet</h2>
        <p style={{ color: "var(--text-muted)", maxWidth: "56ch", margin: "0 auto 20px", lineHeight: 1.6 }}>
          Import your contacts, then write a campaign and send it to an internal
          segment first to confirm the whole loop works before anyone outside the
          company receives anything.
        </p>
        <Link to="/admin/analytics/campaigns/new" className="btn btn-primary">
          Write the first campaign
        </Link>
      </div>
    );
  }

  const rate = data.complaint_rate;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <StatRow>
        <Stat value={data.campaigns_sent} label="Campaigns sent"
              hint={`${data.campaigns_total} in total`} />
        <Stat value={data.sent.toLocaleString()} label="Messages sent" />
        <Stat value={data.verified_engagement.toLocaleString()}
              label="Recipients with verified engagement"
              hint="Confirmed by the landing page, a reply, or the product" />
        <Stat
          value={rate === null ? "—" : `${(rate * 100).toFixed(2)}%`}
          label="Spam complaint rate"
          tone={complaintTone(rate)}
          hint="Providers act at 0.3% and prefer under 0.1%"
        />
      </StatRow>

      {sendTime && (
        <div className="card">
          <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 6 }}>Best time to send</h2>
          {sendTime.enough_data ? (
            <p style={{ fontSize: 14, color: "var(--text)", margin: 0, lineHeight: 1.6 }}>
              Confirmed engagement clusters around{" "}
              <b>{String(sendTime.best_hour_utc).padStart(2, "0")}:00 UTC</b> on{" "}
              <b>{sendTime.best_weekday}</b>, from {sendTime.observations} interactions.
            </p>
          ) : (
            <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0, lineHeight: 1.6 }}>
              {sendTime.note} {sendTime.observations} so far, {sendTime.needed} needed.
            </p>
          )}
        </div>
      )}

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>Recent campaigns</h2>
          <Link to="/admin/analytics/campaigns" style={{ fontSize: 13, color: "var(--accent)" }}>
            All campaigns
          </Link>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <tbody>
              {data.recent.map((c) => (
                <tr key={c.id} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: "12px 20px" }}>
                    <Link to={`/admin/analytics/campaigns/${c.id}`} style={{ fontWeight: 600, color: "var(--text)" }}>
                      {c.name}
                    </Link>
                    <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 2 }}>
                      {c.segment ? `segment: ${c.segment}` : "everyone eligible"}
                    </div>
                  </td>
                  <td style={{ padding: "12px 20px", width: 130 }}>
                    <StatusChip status={c.status} />
                  </td>
                  <td style={{ padding: "12px 20px", width: 170, fontSize: 13, color: "var(--text-muted)" }}>
                    {c.sent_at
                      ? new Date(c.sent_at).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })
                      : "not sent"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
