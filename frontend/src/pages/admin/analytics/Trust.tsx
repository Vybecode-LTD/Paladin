import { useCallback, useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, RefreshCw, Upload } from "lucide-react";
import { api } from "@/lib/api";
import { Section, Stat, StatRow } from "./parts";

/** The domain's standing.
 *
 * Answers the four questions worth checking each morning: is anything sending
 * as us that should not be, are we listed anywhere, where is our mail actually
 * landing, and are complaints near the line that gets a sender blocked.
 *
 * The DMARC section carries the one verdict that gates real work — whether it
 * is safe to tighten the domain policy. Enforcing while a known sender still
 * fails is how a company silently stops receiving its own mail.
 */

interface DmarcSource {
  source_ip: string; header_from: string; messages: number;
  passing: number; failing: number; pass_rate: number;
  dkim_domains: string[]; spf_domains: string[]; reported_by: string[];
}

interface Panel {
  dmarc: {
    has_data: boolean; note?: string; window_days: number;
    sources: DmarcSource[];
    totals: { messages: number; passing: number; failing: number; pass_rate: number;
              sources: number; failing_sources: number };
    safe_to_enforce?: boolean;
  };
  blocklists: {
    has_data: boolean; listed_count: number;
    checks: { target: string; blocklist: string; listed: boolean; response: string; checked_at: string }[];
  };
  placement: {
    has_data: boolean; note?: string; inbox_count?: number;
    campaigns: { id: string; name: string; sent_at: string | null;
                 results: { inbox: string; provider: string; placement: string; detail: string }[] }[];
  };
  complaints: {
    sent: number; complaints: number; hard_bounces: number;
    rate: number | null; bounce_rate: number | null; status: string;
    enforcement_rate: number; target_rate: number;
  };
}

const PLACEMENT_TONE: Record<string, { color: string; label: string }> = {
  inbox: { color: "var(--success)", label: "Inbox" },
  promotions: { color: "var(--warning)", label: "Promotions tab" },
  spam: { color: "var(--danger)", label: "Spam folder" },
  missing: { color: "var(--danger)", label: "Never arrived" },
  error: { color: "var(--text-muted)", label: "Could not check" },
};

export default function Trust() {
  const [data, setData] = useState<Panel | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => {
    api.get("/admin/trust").then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  async function runBlocklists() {
    setBusy("blocklists"); setNote(""); setError("");
    try {
      const r = await api.post("/admin/trust/blocklists/check");
      setNote(`Checked ${r.checked} list(s). ${r.listed} listing(s) found.`);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Check failed");
    } finally {
      setBusy("");
    }
  }

  async function uploadReport(file: File) {
    setBusy("dmarc"); setNote(""); setError("");
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await fetch("/api/admin/trust/dmarc/upload", {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("ab_access_token")}` },
        body,
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Upload failed");
      setNote(`${json.stored} new record(s) stored, ${json.skipped} already seen.`);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy("");
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  if (loading) return <p style={{ color: "var(--text-dim)" }}>Loading…</p>;
  if (!data) return <p style={{ color: "var(--danger)" }}>Could not load the trust panel.</p>;

  const { dmarc, blocklists, placement, complaints } = data;
  const rate = complaints.rate;

  return (
    <div>
      {(note || error) && (
        <p style={{
          fontSize: 14, marginBottom: 16,
          color: error ? "var(--danger)" : "var(--success)",
        }}>{error || note}</p>
      )}

      <Section
        title="Complaints and bounces"
        tier="exact"
        note="The two numbers that get a sending domain blocked. Providers enforce at 0.3% complaints and prefer under 0.1%; on a list of a few hundred a single complaint can cross the first line."
      >
        <StatRow>
          <Stat
            value={rate === null ? "—" : `${(rate * 100).toFixed(2)}%`}
            label="Spam complaint rate"
            tone={complaints.status === "critical" ? "bad" : complaints.status === "warning" ? "warn" : "good"}
            hint={`${complaints.complaints} of ${complaints.sent} messages`}
          />
          <Stat
            value={complaints.bounce_rate === null ? "—" : `${(complaints.bounce_rate * 100).toFixed(2)}%`}
            label="Hard bounce rate"
            tone={(complaints.bounce_rate ?? 0) > 0.02 ? "warn" : "good"}
            hint={`${complaints.hard_bounces} dead addresses. Above 2% looks like a bought list.`}
          />
        </StatRow>
      </Section>

      <Section
        title="Who is sending as the domain"
        tier="exact"
        note={`From the daily DMARC reports every mailbox provider sends. This is the complete list of servers sending mail with the company's name on it, over the last ${dmarc.window_days} days.`}
      >
        {!dmarc.has_data ? (
          <div className="card">
            <p style={{ margin: "0 0 14px", color: "var(--text-muted)", fontSize: 14, lineHeight: 1.6 }}>
              {dmarc.note}
            </p>
            <UploadButton busy={busy === "dmarc"} fileRef={fileRef} onFile={uploadReport} />
          </div>
        ) : (
          <>
            <div
              className="card"
              style={{
                marginBottom: 14, display: "flex", gap: 12, alignItems: "flex-start",
                borderColor: dmarc.safe_to_enforce ? "var(--success)" : "var(--warning)",
              }}
            >
              {dmarc.safe_to_enforce
                ? <CheckCircle2 size={20} style={{ color: "var(--success)", flexShrink: 0, marginTop: 2 }} />
                : <AlertTriangle size={20} style={{ color: "var(--warning)", flexShrink: 0, marginTop: 2 }} />}
              <div>
                <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>
                  {dmarc.safe_to_enforce
                    ? "Every known sender is authenticating"
                    : `${dmarc.totals.failing_sources} source(s) are failing`}
                </div>
                <p style={{ margin: 0, fontSize: 13.5, color: "var(--text-muted)", lineHeight: 1.6, maxWidth: "72ch" }}>
                  {dmarc.safe_to_enforce
                    ? "The domain policy can be tightened a step. Move it to quarantine at 25%, wait a week, and check here again."
                    : "Do not tighten the domain policy yet. Each failing source below is either a legitimate system nobody has authorised, a forwarder, or someone forging the domain — and enforcing before they are told apart is how a company stops receiving its own mail."}
                </p>
              </div>
            </div>

            <div className="card" style={{ padding: 0, overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13.5 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border)" }}>
                    <th style={th}>Source</th>
                    <th style={{ ...th, width: 130 }}>Signed / authorised by</th>
                    <th style={{ ...th, width: 90, textAlign: "right" }}>Messages</th>
                    <th style={{ ...th, width: 100, textAlign: "right" }}>Passing</th>
                  </tr>
                </thead>
                <tbody>
                  {dmarc.sources.map((s) => (
                    <tr key={`${s.source_ip}-${s.header_from}`} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ ...td, fontFamily: "var(--font-mono)", fontSize: 12.5 }}>
                        {s.source_ip}
                        <div style={{ color: "var(--text-dim)", fontSize: 11.5, fontFamily: "var(--font-sans)" }}>
                          as {s.header_from || "—"}
                          {s.reported_by.length > 0 && ` · reported by ${s.reported_by.join(", ")}`}
                        </div>
                      </td>
                      <td style={{ ...td, fontSize: 12, color: "var(--text-muted)" }}>
                        {[...new Set([...s.dkim_domains, ...s.spf_domains])].join(", ") || "nothing"}
                      </td>
                      <td style={{ ...td, textAlign: "right" }}>{s.messages}</td>
                      <td style={{
                        ...td, textAlign: "right", fontWeight: 600,
                        color: s.pass_rate >= 1 ? "var(--success)" : s.pass_rate > 0 ? "var(--warning)" : "var(--danger)",
                      }}>
                        {(s.pass_rate * 100).toFixed(0)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ marginTop: 12 }}>
              <UploadButton busy={busy === "dmarc"} fileRef={fileRef} onFile={uploadReport} />
            </div>
          </>
        )}
      </Section>

      <Section
        title="Blocklists"
        tier="exact"
        note="Public lists that mail servers consult. A listing is sudden and invisible from the sending side: mail simply stops arriving somewhere."
      >
        <div className="card">
          {!blocklists.has_data ? (
            <p style={{ margin: "0 0 14px", color: "var(--text-muted)", fontSize: 14 }}>
              Not checked yet. The worker checks daily once a sending domain is configured.
            </p>
          ) : (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                {blocklists.listed_count === 0
                  ? <CheckCircle2 size={18} style={{ color: "var(--success)" }} />
                  : <AlertTriangle size={18} style={{ color: "var(--danger)" }} />}
                <span style={{ fontWeight: 600, fontSize: 14 }}>
                  {blocklists.listed_count === 0
                    ? "Not listed anywhere"
                    : `Listed on ${blocklists.listed_count} list(s)`}
                </span>
              </div>
              <ul style={{ listStyle: "none", padding: 0, margin: "0 0 14px", fontSize: 13 }}>
                {blocklists.checks.map((c) => (
                  <li key={`${c.target}-${c.blocklist}`} style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", color: c.listed ? "var(--danger)" : "var(--text-muted)" }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>
                      {c.target} · {c.blocklist}
                    </span>
                    <span>{c.listed ? `LISTED (${c.response})` : "clear"}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
          <button type="button" onClick={runBlocklists} disabled={busy === "blocklists"}
                  className="btn btn-ghost" style={{ justifyContent: "center" }}>
            <RefreshCw size={16} /> {busy === "blocklists" ? "Checking…" : "Check now"}
          </button>
        </div>
      </Section>

      <Section
        title="Where our mail landed"
        tier="verified"
        note="Read from mailboxes the company owns that receive every campaign. The only way to see a spam-folder placement before a client mentions it."
      >
        {!placement.has_data ? (
          <div className="card">
            <p style={{ margin: 0, color: "var(--text-muted)", fontSize: 14, lineHeight: 1.6, maxWidth: "72ch" }}>
              {placement.note}
            </p>
          </div>
        ) : (
          <div className="card" style={{ padding: 0 }}>
            {placement.campaigns.map((c) => (
              <div key={c.id} style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)" }}>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{c.name}</div>
                <div style={{ display: "flex", gap: 16, marginTop: 8, flexWrap: "wrap" }}>
                  {c.results.length === 0 ? (
                    <span style={{ fontSize: 13, color: "var(--text-dim)" }}>Not checked yet.</span>
                  ) : c.results.map((r, i) => {
                    const tone = PLACEMENT_TONE[r.placement] ?? PLACEMENT_TONE.error;
                    return (
                      <span key={i} style={{ fontSize: 13, color: tone.color }}>
                        <b>{tone.label}</b>
                        <span style={{ color: "var(--text-dim)" }}> · {r.inbox}</span>
                      </span>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}

function UploadButton({ busy, fileRef, onFile }: {
  busy: boolean;
  fileRef: React.RefObject<HTMLInputElement>;
  onFile: (f: File) => void;
}) {
  return (
    <>
      <input
        ref={fileRef}
        type="file"
        accept=".xml,.gz,.zip"
        style={{ display: "none" }}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
        }}
      />
      <button type="button" onClick={() => fileRef.current?.click()} disabled={busy}
              className="btn btn-ghost" style={{ justifyContent: "center" }}>
        <Upload size={16} /> {busy ? "Reading…" : "Upload a DMARC report"}
      </button>
      <p style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 8, lineHeight: 1.5, maxWidth: "60ch" }}>
        Drag one straight out of the dmarc mailbox — the .xml, .gz or .zip attachment
        from any provider. Once the worker is reading that mailbox this happens on its own.
      </p>
    </>
  );
}

const th: React.CSSProperties = {
  textAlign: "left", padding: "11px 16px", fontSize: 11,
  letterSpacing: ".05em", textTransform: "uppercase", color: "var(--text-muted)",
  fontWeight: 600,
};
const td: React.CSSProperties = { padding: "11px 16px", verticalAlign: "top" };
