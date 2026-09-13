import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Stat, StatRow } from "./parts";

interface Contact {
  id: string; email: string; full_name: string; company: string; country: string;
  consent_basis: string; tracking_consent: boolean; status: string;
  tags: string[]; engagement_score: number; last_engaged_at: string | null;
}

interface Suppression {
  email: string; reason: string; note: string; created_at: string;
}

const CONSENT_LABEL: Record<string, string> = {
  express: "opted in",
  implied: "existing relationship",
  contract: "under contract",
  signup: "signed up",
  demo_request: "requested a demo",
  unknown: "not recorded",
};

const REASON_LABEL: Record<string, string> = {
  unsubscribed: "unsubscribed",
  complained: "marked as spam",
  hard_bounced: "address does not exist",
  manual: "added by an admin",
};

export default function Contacts() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [suppressions, setSuppressions] = useState<Suppression[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/admin/contacts?limit=500"),
      api.get("/admin/suppressions?limit=200"),
    ])
      .then(([c, s]) => { setContacts(c); setSuppressions(s); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ color: "var(--text-dim)" }}>Loading…</p>;

  const filtered = search
    ? contacts.filter((c) =>
        [c.email, c.full_name, c.company].join(" ").toLowerCase().includes(search.toLowerCase()))
    : contacts;

  const mailable = contacts.filter(
    (c) => c.status === "active" && c.consent_basis !== "unknown"
  ).length;
  const noConsent = contacts.filter((c) => c.consent_basis === "unknown").length;
  const trackable = contacts.filter(
    (c) => c.tracking_consent || c.country.toUpperCase() === "US"
  ).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <StatRow>
        <Stat value={contacts.length} label="Contacts" />
        <Stat value={mailable} label="Can be mailed"
              hint="Active, with a consent basis recorded" />
        <Stat value={noConsent} label="No consent recorded"
              tone={noConsent > 0 ? "warn" : "good"}
              hint="Never mailed until a basis is recorded" />
        <Stat value={contacts.length - trackable} label="Open tracking off"
              hint="Outside the US without separate tracking consent" />
      </StatRow>

      <div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name, email or company"
          style={{
            width: "100%", maxWidth: 420, padding: "10px 13px", background: "var(--bg)",
            border: "1px solid var(--border-bright)", borderRadius: "var(--radius-sm)",
            color: "var(--text)", fontSize: 14, marginBottom: 12,
          }}
        />
        <div className="card" style={{ padding: 0, overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13.5 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                <th style={th}>Contact</th>
                <th style={{ ...th, width: 160 }}>Consent</th>
                <th style={{ ...th, width: 130 }}>Tags</th>
                <th style={{ ...th, width: 110 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 200).map((c) => (
                <tr key={c.id} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={td}>
                    <div style={{ fontWeight: 600 }}>{c.full_name || c.email}</div>
                    <div style={{ fontSize: 12.5, color: "var(--text-dim)" }}>
                      {c.email}{c.company && ` · ${c.company}`}{c.country && ` · ${c.country}`}
                    </div>
                  </td>
                  <td style={{ ...td, color: c.consent_basis === "unknown" ? "var(--warning)" : "var(--text-muted)" }}>
                    {CONSENT_LABEL[c.consent_basis] ?? c.consent_basis}
                    {!c.tracking_consent && c.country.toUpperCase() !== "US" && (
                      <div style={{ fontSize: 11.5, color: "var(--text-dim)" }}>no open tracking</div>
                    )}
                  </td>
                  <td style={{ ...td, fontSize: 12.5, color: "var(--text-muted)" }}>
                    {c.tags.join(", ") || "—"}
                  </td>
                  <td style={{ ...td, fontSize: 12.5, color: c.status === "active" ? "var(--text-muted)" : "var(--warning)" }}>
                    {c.status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length > 200 && (
          <p style={{ fontSize: 12.5, color: "var(--text-dim)", marginTop: 8 }}>
            Showing the first 200 of {filtered.length}.
          </p>
        )}
      </div>

      <div>
        <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>Suppression list</h2>
        <p style={{ fontSize: 13, color: "var(--text-muted)", margin: "0 0 12px", maxWidth: "70ch", lineHeight: 1.55 }}>
          Addresses that will never be sent to again. There is deliberately no way to
          remove one from here: an entry means someone asked to stop, or the address
          does not exist, and both should outlive any list import.
        </p>
        {suppressions.length === 0 ? (
          <div className="card" style={{ padding: 24, textAlign: "center" }}>
            <p style={{ color: "var(--text-dim)", margin: 0, fontSize: 13.5 }}>Nobody suppressed yet.</p>
          </div>
        ) : (
          <div className="card" style={{ padding: 0, overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13.5 }}>
              <tbody>
                {suppressions.map((s) => (
                  <tr key={s.email} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={td}>{s.email}</td>
                    <td style={{ ...td, width: 200, color: "var(--text-muted)" }}>
                      {REASON_LABEL[s.reason] ?? s.reason}
                    </td>
                    <td style={{ ...td, width: 140, color: "var(--text-dim)", fontSize: 12.5 }}>
                      {new Date(s.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

const th: React.CSSProperties = {
  textAlign: "left", padding: "11px 16px", fontSize: 11,
  letterSpacing: ".05em", textTransform: "uppercase", color: "var(--text-muted)",
  fontWeight: 600,
};
const td: React.CSSProperties = { padding: "11px 16px", verticalAlign: "top" };
