import { useEffect, useState } from "react";
import { Check, Copy, Plug, Save, Send } from "lucide-react";
import { api } from "@/lib/api";

/** Campaign sender configuration.
 *
 * Deliberately a separate card from the SMTP settings above it, because the
 * two describe different things: SMTP is how a person answers one demo
 * request, this is how the company sends a campaign to a list. Keeping them
 * apart is what lets the campaign provider change without any risk to the
 * demo-reply path, and what lets the two send from different domains with
 * separate reputations.
 *
 * Brought forward from the Analytics phase because the settings have to be
 * enterable before anything can be sent, and the alternative was asking an
 * admin to make an authenticated API call by hand.
 */

type Provider = "smtp" | "mailgun";
type Region = "us" | "eu";

interface SenderSettingsOut {
  provider: Provider;
  mailgun_domain: string;
  mailgun_region: Region;
  api_key_set: boolean;
  webhook_secret_set: boolean;
  from_name: string;
  from_email: string;
  reply_domain: string;
  tracking_base_url: string;
  postal_address: string;
  updated_at: string | null;
}

const EMPTY = {
  provider: "smtp" as Provider,
  mailgun_domain: "",
  mailgun_region: "us" as Region,
  api_key: "",
  webhook_secret: "",
  from_name: "",
  from_email: "",
  reply_domain: "",
  tracking_base_url: "",
  postal_address: "",
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

export default function SenderSettings() {
  const [form, setForm] = useState(EMPTY);
  const [keySet, setKeySet] = useState(false);
  const [secretSet, setSecretSet] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  const [testEmail, setTestEmail] = useState("");
  const [testing, setTesting] = useState(false);
  const [testError, setTestError] = useState("");
  const [testResult, setTestResult] = useState("");
  const [copied, setCopied] = useState(false);

  function apply(data: SenderSettingsOut) {
    setForm({
      provider: data.provider,
      mailgun_domain: data.mailgun_domain,
      mailgun_region: data.mailgun_region,
      // Never populated from the server — secrets are write-only.
      api_key: "",
      webhook_secret: "",
      from_name: data.from_name,
      from_email: data.from_email,
      reply_domain: data.reply_domain,
      tracking_base_url: data.tracking_base_url,
      postal_address: data.postal_address,
    });
    setKeySet(data.api_key_set);
    setSecretSet(data.webhook_secret_set);
  }

  useEffect(() => {
    api.get("/admin/settings/sender")
      .then(apply)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSaved(false);
    try {
      const data: SenderSettingsOut = await api.put("/admin/settings/sender", {
        ...form,
        // Blank means "keep what is stored", matching the SMTP password field.
        api_key: form.api_key ? form.api_key : null,
        webhook_secret: form.webhook_secret ? form.webhook_secret : null,
      });
      apply(data);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  /** `withEmail` false checks credentials and the sending domain without
   * mailing anyone — the safe thing to click repeatedly while getting the
   * configuration right. */
  async function runTest(withEmail: boolean) {
    setTesting(true);
    setTestError("");
    setTestResult("");
    try {
      const res = await api.post("/admin/settings/sender/test", {
        to_email: withEmail ? testEmail : null,
      });
      setTestResult(
        res?.sent
          ? "Connection verified and a test message was sent."
          : "Connection verified. No email was sent."
      );
    } catch (err) {
      setTestError(err instanceof Error ? err.message : "Test failed");
    } finally {
      setTesting(false);
    }
  }

  const webhookUrl = form.tracking_base_url
    ? `${form.tracking_base_url.replace(/\/+$/, "")}/api/webhooks/mailgun`
    : "";

  async function copyWebhook() {
    try {
      await navigator.clipboard.writeText(webhookUrl);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      // Clipboard access can be refused; the URL is on screen to copy by hand.
    }
  }

  if (loading) return <p style={{ color: "var(--text-dim)" }}>Loading…</p>;

  const isMailgun = form.provider === "mailgun";

  return (
    <div
      className="admin-grid-2col"
      style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 24, alignItems: "start" }}
    >
      <form onSubmit={submit} className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700 }}>Campaign sender</h3>

        <div>
          <label style={labelStyle}>Provider</label>
          <select
            style={inputStyle}
            value={form.provider}
            onChange={(e) => setForm({ ...form, provider: e.target.value as Provider })}
          >
            <option value="mailgun">Mailgun</option>
            <option value="smtp">SMTP (internal test sends only)</option>
          </select>
          <p style={hintStyle}>
            {isMailgun
              ? "Mailgun reports delivery, bounces and spam complaints back to the dashboard. Raw SMTP reports none of those."
              : "SMTP reuses the credentials above and reports only that the relay accepted the message — no delivery confirmation, no bounces, no complaints. Suitable for sending to an internal test segment, not to clients."}
          </p>
        </div>

        {isMailgun && (
          <>
            <div>
              <label style={labelStyle}>Sending domain</label>
              <input
                style={inputStyle}
                value={form.mailgun_domain}
                placeholder="updates.ashfordbriggs.com"
                onChange={(e) => setForm({ ...form, mailgun_domain: e.target.value })}
              />
              <p style={hintStyle}>
                A bare domain, not a URL. This must <strong>not</strong> be the domain used for
                the product's password and PIN emails — sharing one would put campaign
                complaints on the reputation that delivers a client's password reset.
              </p>
            </div>

            <div>
              <label style={labelStyle}>Region</label>
              <select
                style={inputStyle}
                value={form.mailgun_region}
                onChange={(e) => setForm({ ...form, mailgun_region: e.target.value as Region })}
              >
                <option value="us">US</option>
                <option value="eu">EU</option>
              </select>
              <p style={hintStyle}>
                Must match the region the Mailgun account is in. A key from the wrong region
                fails with a confusing authorisation error.
              </p>
            </div>

            <div>
              <label style={labelStyle}>API key</label>
              <input
                type="password"
                style={inputStyle}
                value={form.api_key}
                placeholder={keySet ? "Leave blank to keep existing key" : ""}
                onChange={(e) => setForm({ ...form, api_key: e.target.value })}
              />
              {keySet && <p style={hintStyle}>A key is already saved — leave blank to keep it.</p>}
            </div>

            <div>
              <label style={labelStyle}>Webhook signing key</label>
              <input
                type="password"
                style={inputStyle}
                value={form.webhook_secret}
                placeholder={secretSet ? "Leave blank to keep existing key" : ""}
                onChange={(e) => setForm({ ...form, webhook_secret: e.target.value })}
              />
              <p style={hintStyle}>
                <strong>A different credential from the API key.</strong> In Mailgun it is under
                Settings, API keys, "HTTP webhook signing key". Putting the API key here means
                every incoming event is rejected and the dashboard silently shows no deliveries
                or bounces at all.
                {secretSet && " A key is already saved — leave blank to keep it."}
              </p>
            </div>
          </>
        )}

        <div>
          <label style={labelStyle}>From name</label>
          <input
            style={inputStyle}
            value={form.from_name}
            placeholder="Matt at Ashford &amp; Briggs"
            onChange={(e) => setForm({ ...form, from_name: e.target.value })}
          />
        </div>

        <div>
          <label style={labelStyle}>From email</label>
          <input
            type="email"
            style={inputStyle}
            value={form.from_email}
            placeholder="matt@updates.ashfordbriggs.com"
            onChange={(e) => setForm({ ...form, from_email: e.target.value })}
          />
          <p style={hintStyle}>
            Chosen once and never varied. Consistency is itself a reputation signal, and this is
            the address recipients add to their contacts. Replies come back to it, so it must
            receive mail: a Google Workspace mailbox, or an address on the sending domain with
            Mailgun forwarding replies to a person.
          </p>
        </div>

        <div>
          <label style={labelStyle}>Reply domain</label>
          <input
            style={inputStyle}
            value={form.reply_domain}
            placeholder="Leave blank for now"
            onChange={(e) => setForm({ ...form, reply_domain: e.target.value })}
          />
          <p style={hintStyle}>
            <strong>Leave this blank.</strong> Nothing records replies yet, so with a domain here
            every reply goes to a per-message address that no one reads. When it is blank,
            replies go to the From address.
          </p>
        </div>

        <div>
          <label style={labelStyle}>Tracking URL</label>
          <input
            style={inputStyle}
            value={form.tracking_base_url}
            placeholder="https://links.ashfordbriggs.com"
            onChange={(e) => setForm({ ...form, tracking_base_url: e.target.value })}
          />
          <p style={hintStyle}>
            Where unsubscribe and tracking links point. Must be reachable over HTTPS from
            outside, because it is printed inside mail that cannot be changed once sent. Use a
            hostname that never gets mail records, not the sending domain: once Mailgun's DNS
            records are published on a name, it stops resolving to a web server.
          </p>
        </div>

        <div>
          <label style={labelStyle}>Postal address</label>
          <input
            style={inputStyle}
            value={form.postal_address}
            placeholder="Ashford &amp; Briggs, Jacksonville, FL"
            onChange={(e) => setForm({ ...form, postal_address: e.target.value })}
          />
          <p style={hintStyle}>
            Printed in the footer of every campaign. US law requires a valid physical address on
            marketing email, so a campaign cannot be sent without one.
          </p>
        </div>

        {error && <p style={{ color: "var(--danger)", fontSize: 14 }}>{error}</p>}
        {saved && !error && <p style={{ color: "var(--success)", fontSize: 14 }}>Settings saved.</p>}
        <button type="submit" disabled={saving} className="btn btn-primary" style={{ justifyContent: "center" }}>
          <Save size={16} /> {saving ? "Saving…" : "Save campaign sender"}
        </button>
      </form>

      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>Check the connection</h3>
          <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0, lineHeight: 1.5 }}>
            Verifies the credentials and confirms the sending domain exists on the account. Sends
            nothing, so it is safe to click while getting the settings right.
          </p>
          <button
            type="button"
            onClick={() => runTest(false)}
            disabled={testing}
            className="btn btn-ghost"
            style={{ justifyContent: "center" }}
          >
            <Plug size={16} /> {testing ? "Checking…" : "Check connection"}
          </button>

          <div style={{ borderTop: "1px solid var(--border)", paddingTop: 14 }}>
            <label style={labelStyle}>Or send a real test message to</label>
            <input
              type="email"
              style={inputStyle}
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
            />
            <button
              type="button"
              onClick={() => runTest(true)}
              disabled={testing || !testEmail}
              className="btn btn-ghost"
              style={{ justifyContent: "center", width: "100%", marginTop: 10 }}
            >
              <Send size={16} /> {testing ? "Sending…" : "Send test message"}
            </button>
          </div>

          {testError && <p style={{ color: "var(--danger)", fontSize: 14 }}>{testError}</p>}
          {testResult && !testError && (
            <p style={{ color: "var(--success)", fontSize: 14 }}>{testResult}</p>
          )}
        </div>

        {isMailgun && (
          <div className="card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700 }}>Webhook URL</h3>
            <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0, lineHeight: 1.5 }}>
              Paste this into Mailgun under Sending, Webhooks, for each of Delivered, Permanent
              Failure, Temporary Failure, Complained and Unsubscribed. Without it the dashboard
              can show what was accepted for sending and nothing about what happened next.
            </p>
            {webhookUrl ? (
              <>
                <code
                  style={{
                    display: "block", fontSize: 12, wordBreak: "break-all",
                    background: "var(--bg)", padding: "10px 12px",
                    borderRadius: "var(--radius-sm)", border: "1px solid var(--border)",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {webhookUrl}
                </code>
                <button
                  type="button"
                  onClick={copyWebhook}
                  className="btn btn-ghost"
                  style={{ justifyContent: "center" }}
                >
                  {copied ? <Check size={16} /> : <Copy size={16} />}
                  {copied ? "Copied" : "Copy URL"}
                </button>
              </>
            ) : (
              <p style={{ fontSize: 13, color: "var(--text-dim)", margin: 0 }}>
                Set the tracking URL and save to see the webhook address.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
