import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Save, Send, Users } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { StatusChip } from "./parts";

interface Campaign {
  id: string; name: string; subject: string; preheader: string;
  body_markdown: string; segment: string; variant_b_subject: string;
  holdout_percent: number; status: string; error: string;
}

interface AudiencePreview {
  total_contacts: number;
  eligible: number;
  suppressed: number;
  excluded_inactive: number;
  excluded_no_consent: number;
  holdout: number;
  variant_a: number;
  variant_b: number;
  untrackable: number;
  sample: { email: string; full_name: string; variant: string; trackable: boolean }[];
}

const EMPTY = {
  name: "", subject: "", preheader: "", body_markdown: "",
  segment: "", variant_b_subject: "", holdout_percent: 0,
};

const inputStyle: React.CSSProperties = {
  width: "100%", padding: "11px 13px", background: "var(--bg)",
  border: "1px solid var(--border-bright)", borderRadius: "var(--radius-sm)",
  color: "var(--text)", fontSize: 15, fontFamily: "var(--font-sans)",
};
const labelStyle: React.CSSProperties = {
  fontSize: 13, color: "var(--text-muted)", display: "block", marginBottom: 6,
};
const hintStyle: React.CSSProperties = {
  fontSize: 12, color: "var(--text-dim)", marginTop: 6, lineHeight: 1.5,
};

export default function CampaignEditor() {
  const { id } = useParams<{ id: string }>();
  const nav = useNavigate();
  const { user } = useAuth();

  const [form, setForm] = useState(EMPTY);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [tags, setTags] = useState<string[]>([]);
  const [audience, setAudience] = useState<AudiencePreview | null>(null);
  const [loading, setLoading] = useState(Boolean(id));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  const [testEmail, setTestEmail] = useState("");
  const [testing, setTesting] = useState(false);
  const [testNote, setTestNote] = useState("");
  const [queueing, setQueueing] = useState(false);

  const isAdmin = user?.role === "admin";
  const editable = !campaign || campaign.status === "draft" || campaign.status === "failed";

  useEffect(() => {
    api.get("/admin/contacts/tags").then(setTags).catch(() => {});
  }, []);

  const loadAudience = useCallback(() => {
    if (!id) return;
    api.get(`/admin/campaigns/${id}/audience`).then(setAudience).catch(() => {});
  }, [id]);

  useEffect(() => {
    if (!id) return;
    api.get(`/admin/campaigns/${id}`)
      .then((c: Campaign) => {
        setCampaign(c);
        setForm({
          name: c.name, subject: c.subject, preheader: c.preheader,
          body_markdown: c.body_markdown, segment: c.segment,
          variant_b_subject: c.variant_b_subject, holdout_percent: c.holdout_percent,
        });
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load"))
      .finally(() => setLoading(false));
    loadAudience();
  }, [id, loadAudience]);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true); setError(""); setSaved(false);
    try {
      if (id) {
        const c = await api.patch(`/admin/campaigns/${id}`, form);
        setCampaign(c);
        setSaved(true);
        loadAudience();
      } else {
        const c: Campaign = await api.post("/admin/campaigns", form);
        nav(`/admin/analytics/campaigns/${c.id}/edit`, { replace: true });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function sendTest() {
    setTesting(true); setTestNote(""); setError("");
    try {
      await api.post(`/admin/campaigns/${id}/test`, { to_email: testEmail });
      setTestNote(`Test sent to ${testEmail}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Test failed");
    } finally {
      setTesting(false);
    }
  }

  async function queue() {
    if (!audience) return;
    const ok = window.confirm(
      `Queue this campaign to ${audience.eligible} recipient(s)?\n\n` +
      `Sending cannot be undone — messages handed to the provider cannot be recalled.`
    );
    if (!ok) return;
    setQueueing(true); setError("");
    try {
      const c = await api.post(`/admin/campaigns/${id}/send`, { scheduled_for: null });
      setCampaign(c);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not queue the campaign");
    } finally {
      setQueueing(false);
    }
  }

  if (loading) return <p style={{ color: "var(--text-dim)" }}>Loading…</p>;

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Link to="/admin/analytics/campaigns" style={{ fontSize: 13, color: "var(--accent)" }}>
          ← All campaigns
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 8, flexWrap: "wrap" }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>
            {id ? form.name || "Campaign" : "New campaign"}
          </h2>
          {campaign && <StatusChip status={campaign.status} />}
        </div>
      </div>

      {!editable && (
        <div className="card" style={{ marginBottom: 20, borderColor: "var(--warning)" }}>
          <p style={{ margin: 0, fontSize: 14, color: "var(--warning)", lineHeight: 1.55 }}>
            This campaign is {campaign?.status} and can no longer be edited. Messages
            already handed to the provider cannot be recalled, so allowing a change now
            would mean one list receiving two different emails under one name.
          </p>
        </div>
      )}

      <div className="admin-grid-2col" style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 24, alignItems: "start" }}>
        <form onSubmit={save} className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <label style={labelStyle}>Internal name</label>
            <input required disabled={!editable} style={inputStyle} value={form.name}
                   onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <p style={hintStyle}>Only ever seen here, not by recipients.</p>
          </div>

          <div>
            <label style={labelStyle}>Subject</label>
            <input disabled={!editable} style={inputStyle} value={form.subject}
                   onChange={(e) => setForm({ ...form, subject: e.target.value })} />
          </div>

          <div>
            <label style={labelStyle}>Preview text</label>
            <input disabled={!editable} style={inputStyle} value={form.preheader}
                   onChange={(e) => setForm({ ...form, preheader: e.target.value })} />
            <p style={hintStyle}>
              Shown after the subject in most inboxes. Without it, clients pull the first
              line of the body, which is usually the greeting.
            </p>
          </div>

          <div>
            <label style={labelStyle}>Body</label>
            <textarea
              disabled={!editable}
              style={{ ...inputStyle, minHeight: 300, fontFamily: "var(--font-mono)", fontSize: 13.5, lineHeight: 1.6, resize: "vertical" }}
              value={form.body_markdown}
              onChange={(e) => setForm({ ...form, body_markdown: e.target.value })}
            />
            <p style={hintStyle}>
              Markdown. Use <code>{"{{first_name}}"}</code>, <code>{"{{full_name}}"}</code>,{" "}
              <code>{"{{company}}"}</code> to personalise — a missing name renders a neutral
              greeting rather than an empty gap. The postal address and unsubscribe link are
              added automatically; you do not need to write them.
            </p>
          </div>

          <div>
            <label style={labelStyle}>Send to</label>
            <select disabled={!editable} style={inputStyle} value={form.segment}
                    onChange={(e) => setForm({ ...form, segment: e.target.value })}>
              <option value="">Everyone eligible</option>
              {tags.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <p style={hintStyle}>
              Resolved when the campaign actually sends, not now — so anyone who
              unsubscribes in the meantime is excluded automatically.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <div>
              <label style={labelStyle}>Variant B subject</label>
              <input disabled={!editable} style={inputStyle} value={form.variant_b_subject}
                     onChange={(e) => setForm({ ...form, variant_b_subject: e.target.value })} />
              <p style={hintStyle}>Leave blank for no A/B test.</p>
            </div>
            <div>
              <label style={labelStyle}>Holdout %</label>
              <input type="number" min={0} max={50} disabled={!editable} style={inputStyle}
                     value={form.holdout_percent}
                     onChange={(e) => setForm({ ...form, holdout_percent: Number(e.target.value) })} />
              <p style={hintStyle}>Held back entirely, as a baseline to measure against.</p>
            </div>
          </div>

          {error && <p style={{ color: "var(--danger)", fontSize: 14 }}>{error}</p>}
          {saved && !error && <p style={{ color: "var(--success)", fontSize: 14 }}>Saved.</p>}

          {editable && (
            <button type="submit" disabled={saving} className="btn btn-primary" style={{ justifyContent: "center" }}>
              <Save size={16} /> {saving ? "Saving…" : id ? "Save draft" : "Create campaign"}
            </button>
          )}
        </form>

        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {id && audience && (
            <div className="card">
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 4, display: "flex", alignItems: "center", gap: 8 }}>
                <Users size={16} /> Who will receive this
              </h3>
              <p style={{ fontSize: 12.5, color: "var(--text-dim)", margin: "0 0 14px", lineHeight: 1.5 }}>
                Checked again at send time. The figures below account for every contact
                in the segment, so nobody disappears without a reason.
              </p>

              <div style={{ fontSize: 32, fontWeight: 700, lineHeight: 1, color: "var(--accent)" }}>
                {audience.eligible}
              </div>
              <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 14 }}>
                will actually be sent to
              </div>

              <ul style={{ listStyle: "none", padding: 0, margin: 0, fontSize: 13.5 }}>
                <Row label="In this segment" value={audience.total_contacts} />
                <Row label="No consent recorded" value={-audience.excluded_no_consent} muted />
                <Row label="Unsubscribed or bounced" value={-audience.excluded_inactive} muted />
                <Row label="On the suppression list" value={-audience.suppressed} muted />
                <Row label="Eligible" value={audience.eligible} strong />
                {audience.holdout > 0 && (
                  <Row label="Held back as a control" value={-audience.holdout} muted />
                )}
              </ul>

              {audience.untrackable > 0 && (
                <p style={{ fontSize: 12.5, color: "var(--text-dim)", marginTop: 12, lineHeight: 1.5 }}>
                  {audience.untrackable} of them will receive no tracking pixel, because
                  they are outside the US and have not consented to open tracking.
                </p>
              )}

              {audience.variant_b > 0 && (
                <p style={{ fontSize: 12.5, color: "var(--text-muted)", marginTop: 10 }}>
                  Split {audience.variant_a} / {audience.variant_b} between variants A and B.
                </p>
              )}
            </div>
          )}

          {id && editable && (
            <div className="card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>Send a test</h3>
              <p style={{ fontSize: 12.5, color: "var(--text-dim)", margin: 0, lineHeight: 1.5 }}>
                The real message, to one address. Creates no records and cannot affect this
                campaign's numbers.
              </p>
              <input type="email" style={inputStyle} value={testEmail} placeholder="you@example.com"
                     onChange={(e) => setTestEmail(e.target.value)} />
              <button type="button" onClick={sendTest} disabled={testing || !testEmail}
                      className="btn btn-ghost" style={{ justifyContent: "center" }}>
                <Send size={16} /> {testing ? "Sending…" : "Send test"}
              </button>
              {testNote && <p style={{ color: "var(--success)", fontSize: 13, margin: 0 }}>{testNote}</p>}
            </div>
          )}

          {id && editable && (
            <div className="card" style={{ display: "flex", flexDirection: "column", gap: 12, borderColor: "var(--accent)" }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>Send the campaign</h3>
              {isAdmin ? (
                <>
                  <p style={{ fontSize: 12.5, color: "var(--text-dim)", margin: 0, lineHeight: 1.5 }}>
                    Queues it for the send worker. Messages handed to the provider cannot
                    be recalled, so check the audience above first.
                  </p>
                  <button type="button" onClick={queue}
                          disabled={queueing || !audience || audience.eligible === 0}
                          className="btn btn-primary" style={{ justifyContent: "center" }}>
                    <Send size={16} />
                    {queueing ? "Queueing…" : `Queue to ${audience?.eligible ?? 0} recipients`}
                  </button>
                </>
              ) : (
                <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0, lineHeight: 1.55 }}>
                  Only an admin can send a campaign. Drafting and testing are open to
                  editors; putting mail in front of real clients is the step worth
                  restricting.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, muted, strong }: {
  label: string; value: number; muted?: boolean; strong?: boolean;
}) {
  if (value === 0 && muted) return null;
  return (
    <li style={{
      display: "flex", justifyContent: "space-between", padding: "6px 0",
      borderTop: strong ? "1px solid var(--border)" : undefined,
      marginTop: strong ? 6 : undefined,
      color: muted ? "var(--text-muted)" : "var(--text)",
      fontWeight: strong ? 600 : 400,
    }}>
      <span>{label}</span>
      <span style={{ fontVariantNumeric: "tabular-nums" }}>
        {value < 0 ? value : value}
      </span>
    </li>
  );
}
