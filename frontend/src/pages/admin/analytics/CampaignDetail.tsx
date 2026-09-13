import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "@/lib/api";
import {
  Breakdown, Section, SplitBar, Stat, StatRow, StatusChip,
} from "./parts";
import { pct } from "./format";

/** The scorecard.
 *
 * The one screen this whole system exists to produce. Every figure carries
 * its tier, and the two inferred ones — opens and clicks — are shown as a
 * split between probable machines and possible people, never as a single
 * total. A bought tool would report the total, and the total is about half
 * automatic prefetch.
 */

interface SplitFigure {
  recorded: number;
  machine: number;
  possibly_human: number;
  machine_breakdown: Record<string, number>;
  other_breakdown: Record<string, number>;
  unique_recipients: number;
  measurable?: number;
  not_measurable?: number;
  verified_recipients?: number;
}

interface Scorecard {
  campaign: {
    id: string; name: string; subject: string; status: string;
    segment: string; sent_at: string | null; holdout_percent: number;
  };
  delivery: {
    messages: number; sent: number; holdout: number; failed: number;
    trackable: number; delivered: number; soft_bounced: number;
    hard_bounced: number; complained: number; unsubscribed: number;
  };
  opens: SplitFigure;
  clicks: SplitFigure;
  links: { index: number; url: string; clicks: number; machine: number; possibly_human: number }[];
  replies: { total: number; auto_replies: number };
  conversions: { total: number; by_name: Record<string, number> };
  ab: null | {
    a: { sent: number; verified_clicks: number };
    b: { sent: number; verified_clicks: number };
    metric: string;
    p_value: number | null;
    significant: boolean;
    verdict: string;
  };
}

export default function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<Scorecard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    api.get(`/admin/analytics/campaigns/${id}`)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load this campaign"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p style={{ color: "var(--text-dim)" }}>Loading…</p>;
  if (error) return <p style={{ color: "var(--danger)" }}>{error}</p>;
  if (!data) return null;

  const { campaign, delivery, opens, clicks, links, replies, conversions, ab } = data;
  const bounced = delivery.hard_bounced + delivery.soft_bounced;

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Link to="/admin/analytics/campaigns" style={{ fontSize: 13, color: "var(--accent)" }}>
          ← All campaigns
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 8, flexWrap: "wrap" }}>
          <h2 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>{campaign.name}</h2>
          <StatusChip status={campaign.status} />
        </div>
        <p style={{ fontSize: 14, color: "var(--text-muted)", margin: "6px 0 0" }}>
          {campaign.subject}
          {campaign.sent_at && ` · sent ${new Date(campaign.sent_at).toLocaleDateString()}`}
          {campaign.segment && ` · segment: ${campaign.segment}`}
        </p>
      </div>

      <Section
        title="Delivery"
        tier="exact"
        note="Reported by the mail system itself. These figures cannot be wrong."
      >
        <StatRow>
          <Stat value={delivery.sent} label="Sent"
                hint={delivery.holdout > 0 ? `${delivery.holdout} held back as a control` : undefined} />
          <Stat value={delivery.delivered} label="Delivered"
                hint={delivery.sent ? pct(delivery.delivered, delivery.sent) : undefined} />
          <Stat value={bounced} label="Bounced"
                tone={delivery.hard_bounced > 0 ? "warn" : undefined}
                hint={`${delivery.hard_bounced} hard, ${delivery.soft_bounced} soft`} />
          <Stat value={delivery.complained} label="Spam complaints"
                tone={delivery.complained > 0 ? "bad" : "good"}
                hint={delivery.unsubscribed > 0 ? `${delivery.unsubscribed} unsubscribed` : undefined} />
        </StatRow>
        {delivery.failed > 0 && (
          <p style={{ fontSize: 13, color: "var(--warning)", marginTop: 10 }}>
            {delivery.failed} message{delivery.failed === 1 ? "" : "s"} could not be sent at all.
          </p>
        )}
      </Section>

      <Section
        title="Opens"
        tier="inferred"
        note="A pixel fetch is something a machine does perfectly, so an open is never proof that a person read anything. What we can do is name the machines we recognise."
      >
        <div className="card">
          <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 16 }}>
            <Stat value={opens.recorded} label="Opens recorded" />
            <Stat value={opens.unique_recipients} label="Distinct recipients" />
            <Stat
              value={opens.measurable ?? 0}
              label="Messages carrying a pixel"
              hint={
                (opens.not_measurable ?? 0) > 0
                  ? `${opens.not_measurable} recipients have not consented to open tracking`
                  : undefined
              }
            />
          </div>
          <SplitBar machine={opens.machine} human={opens.possibly_human} />
          <Breakdown items={opens.machine_breakdown} />
          {(opens.not_measurable ?? 0) > 0 && (
            <p style={{ fontSize: 12.5, color: "var(--text-dim)", marginTop: 12, lineHeight: 1.55, maxWidth: "70ch" }}>
              An open rate here would have the wrong denominator. {opens.not_measurable} of
              the {delivery.sent} recipients were never measurable, because they have not
              consented to open tracking, so they cannot be counted as people who did not open.
            </p>
          )}
        </div>
      </Section>

      <Section
        title="Clicks"
        tier="inferred"
        note="Security products fetch every link in an email before the recipient sees it, forwarding the recipient's own browser string. Only the landing page's beacon, which needs JavaScript to run, tells the two apart."
      >
        <div className="card">
          <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 16 }}>
            <Stat value={clicks.recorded} label="Clicks recorded" />
            <Stat value={clicks.unique_recipients} label="Distinct recipients" />
            <Stat
              value={clicks.verified_recipients ?? 0}
              label="Verified by the landing page"
              tone={(clicks.verified_recipients ?? 0) > 0 ? "good" : undefined}
              hint="A real browser rendered the page"
            />
          </div>
          <SplitBar
            machine={clicks.machine}
            human={clicks.possibly_human}
            humanLabel="not identified as a machine"
          />
          <Breakdown items={clicks.machine_breakdown} />
        </div>
      </Section>

      {links.length > 0 && (
        <Section title="By link" tier="inferred"
                 note="Which destination people actually used, with scanner traffic separated out.">
          <div className="card" style={{ padding: 0, overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13.5 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  <th style={th}>Destination</th>
                  <th style={{ ...th, width: 110, textAlign: "right" }}>Not a machine</th>
                  <th style={{ ...th, width: 100, textAlign: "right" }}>Machine</th>
                </tr>
              </thead>
              <tbody>
                {links.map((l) => (
                  <tr key={l.index} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ ...td, wordBreak: "break-all", fontFamily: "var(--font-mono)", fontSize: 12.5 }}>
                      {l.url}
                    </td>
                    <td style={{ ...td, textAlign: "right", fontWeight: 600 }}>{l.possibly_human}</td>
                    <td style={{ ...td, textAlign: "right", color: "var(--text-muted)" }}>{l.machine}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      <Section
        title="Replies and conversions"
        tier="verified"
        note="A person wrote something, or used the product. Nothing here can be produced by a scanner."
      >
        <StatRow>
          <Stat value={replies.total} label="Replies"
                tone={replies.total > 0 ? "good" : undefined}
                hint={replies.auto_replies > 0 ? `${replies.auto_replies} out-of-office, not counted` : undefined} />
          <Stat value={conversions.total} label="Actions in Paladin"
                tone={conversions.total > 0 ? "good" : undefined}
                hint={
                  Object.keys(conversions.by_name).length > 0
                    ? Object.entries(conversions.by_name).map(([n, c]) => `${n.replace(/_/g, " ")} ${c}`).join(" · ")
                    : "Nothing reported by the product yet"
                } />
        </StatRow>
      </Section>

      {ab && (
        <Section title="A/B test" tier="derived"
                 note={`Measured on ${ab.metric}. Not on opens: a subject line is meant to influence opens, but opens are the least trustworthy figure here, so testing on them would measure which subject the prefetchers preferred.`}>
          <div className="card">
            <div style={{ display: "flex", gap: 32, flexWrap: "wrap", marginBottom: 16 }}>
              <Stat value={pct(ab.a.verified_clicks, ab.a.sent)} label="Variant A"
                    hint={`${ab.a.verified_clicks} of ${ab.a.sent} sent`} />
              <Stat value={pct(ab.b.verified_clicks, ab.b.sent)} label="Variant B"
                    hint={`${ab.b.verified_clicks} of ${ab.b.sent} sent`} />
            </div>
            <p style={{
              fontSize: 14, lineHeight: 1.6, margin: 0, padding: "12px 16px",
              borderRadius: 6, background: "var(--bg-elevated)",
              color: ab.significant ? "var(--success)" : "var(--text-muted)",
            }}>
              {ab.verdict}
              {ab.p_value !== null && (
                <span style={{ color: "var(--text-dim)", fontSize: 12.5 }}> (p = {ab.p_value})</span>
              )}
            </p>
          </div>
        </Section>
      )}
    </div>
  );
}

const th: React.CSSProperties = {
  textAlign: "left", padding: "11px 16px", fontSize: 11,
  letterSpacing: ".05em", textTransform: "uppercase", color: "var(--text-muted)",
  fontWeight: 600,
};
const td: React.CSSProperties = { padding: "11px 16px", verticalAlign: "top" };
