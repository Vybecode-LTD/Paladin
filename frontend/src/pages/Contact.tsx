import { useState } from "react";
import { motion } from "framer-motion";
import { Mail, Phone, Linkedin, MapPin } from "lucide-react";
import { api } from "@/lib/api";
import Seo from "@/components/Seo";
import Waveform from "@/components/Waveform";
import { useFadeUp } from "@/hooks/useReveal";

const ROLES = ["Recruiter", "Recruiting Manager", "HR Director or VP", "Staffing Agency Owner", "Executive — C-Suite", "Other"];
const SIZES = ["1–5", "6–20", "21–50", "50+"];

export default function Contact() {
  const fadeUp = useFadeUp();
  const [form, setForm] = useState({
    full_name: "", company: "", email: "", phone: "", role: "", team_size: "", message: "",
  });
  const [status, setStatus] = useState<"idle" | "sending" | "done" | "error">("idle");
  const [error, setError] = useState("");

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm({ ...form, [k]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("sending");
    setError("");
    try {
      await api.post("/demo-requests", form);
      setStatus("done");
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Something went wrong");
    }
  }

  return (
    <>
      <Seo
        title="Request a Demo | Ashford & Briggs"
        description="See Paladin live on a real recruiting call. Tell us about your team and we'll set up a demo of real-time AI intelligence for recruiter phone calls."
        path="/contact"
      />
      <section style={{ padding: "90px 0 60px" }} className="container">
        <div className="contact-grid">
          {/* Left: pitch + channels */}
          <motion.div {...fadeUp}>
            <span className="eyebrow">Contact</span>
            <h1 style={{ fontSize: "clamp(34px, 5vw, 56px)", fontWeight: 800, letterSpacing: "-0.03em", margin: "16px 0 18px" }}>
              See Paladin on a <span className="gradient-text">live call.</span>
            </h1>
            <p style={{ fontSize: 18, color: "var(--text-muted)", marginBottom: 36 }}>
              The fastest way to understand Paladin is to watch the Intelligence Pane work
              on a real recruiting scenario. Tell us a little about your team and we'll set
              it up.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {[
                { icon: Mail, glyph: "blue", label: "General inquiries", value: "inquiries@ashfordbriggs.com", href: "mailto:inquiries@ashfordbriggs.com" },
                { icon: Mail, glyph: "violet", label: "Sales & trials", value: "info@ashfordbriggs.com", href: "mailto:info@ashfordbriggs.com" },
                { icon: Phone, glyph: "cyan", label: "Matt Barker", value: "mbarker@ashfordbriggs.com · (603) 556-8277", href: "tel:+16035568277" },
                { icon: Mail, glyph: "coral", label: "John Evans", value: "jevans@ashfordbriggs.com", href: "mailto:jevans@ashfordbriggs.com" },
                { icon: Linkedin, glyph: "amber", label: "LinkedIn", value: "ashford-briggs-llc", href: "https://linkedin.com/company/ashford-briggs-llc" },
                { icon: MapPin, glyph: "coral", label: "HQ", value: "Jacksonville, FL · Founded 2026", href: undefined },
              ].map((c) => (
                <div key={c.label} style={{ display: "flex", alignItems: "center", gap: 14 }}>
                  <div className={`glyph-badge glyph-${c.glyph}`} style={{ width: 40, height: 40, flexShrink: 0 }}>
                    <c.icon size={18} color="currentColor" aria-hidden="true" />
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: "var(--text-dim)", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>{c.label}</div>
                    {c.href ? <a href={c.href} style={{ fontSize: 15, color: "var(--text-muted)" }}>{c.value}</a>
                      : <div style={{ fontSize: 15, color: "var(--text-muted)" }}>{c.value}</div>}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Right: form */}
          <motion.div {...fadeUp} transition={{ duration: 0.5, delay: 0.1 }} className="card" style={{ padding: 32 }}>
            {status === "done" ? (
              <div style={{ textAlign: "center", padding: "40px 0" }}>
                <div style={{ display: "flex", justifyContent: "center", marginBottom: 16 }}>
                  <Waveform frozen />
                </div>
                <h3 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>Signal received.</h3>
                <p style={{ color: "var(--text-muted)" }}>A real person will reach out to schedule. No spam, promise.</p>
              </div>
            ) : (
              <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                <div>
                  <label htmlFor="contact-full-name" style={{ fontSize: 13, color: "var(--text-muted)", display: "block", marginBottom: 6 }}>Full Name *</label>
                  <input id="contact-full-name" required maxLength={200} className="field-underline" value={form.full_name} onChange={set("full_name")} />
                </div>
                <div>
                  <label htmlFor="contact-company" style={{ fontSize: 13, color: "var(--text-muted)", display: "block", marginBottom: 6 }}>Company *</label>
                  <input id="contact-company" required maxLength={200} className="field-underline" value={form.company} onChange={set("company")} />
                </div>
                <div>
                  <label htmlFor="contact-email" style={{ fontSize: 13, color: "var(--text-muted)", display: "block", marginBottom: 6 }}>Work Email *</label>
                  <input id="contact-email" required type="email" maxLength={200} className="field-underline" value={form.email} onChange={set("email")} />
                </div>
                <div>
                  <label htmlFor="contact-phone" style={{ fontSize: 13, color: "var(--text-muted)", display: "block", marginBottom: 6 }}>Phone</label>
                  <input id="contact-phone" type="tel" placeholder="(555) 123-4567" maxLength={30} className="field-underline" value={form.phone} onChange={set("phone")} />
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                  <div>
                    <label htmlFor="contact-role" style={{ fontSize: 13, color: "var(--text-muted)", display: "block", marginBottom: 6 }}>Role</label>
                    <select id="contact-role" className="field-underline" value={form.role} onChange={set("role")}>
                      <option value="">Select…</option>
                      {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </div>
                  <div>
                    <label htmlFor="contact-team-size" style={{ fontSize: 13, color: "var(--text-muted)", display: "block", marginBottom: 6 }}>Team Size</label>
                    <select id="contact-team-size" className="field-underline" value={form.team_size} onChange={set("team_size")}>
                      <option value="">Select…</option>
                      {SIZES.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label htmlFor="contact-message" style={{ fontSize: 13, color: "var(--text-muted)", display: "block", marginBottom: 6 }}>Anything you'd like us to know?</label>
                  <textarea id="contact-message" rows={3} maxLength={2000} className="field-underline" style={{ resize: "vertical" }} value={form.message} onChange={set("message")} />
                </div>
                {status === "error" && <p role="alert" style={{ color: "var(--danger)", fontSize: 14 }}>{error}</p>}
                <button type="submit" disabled={status === "sending"} className="btn btn-primary" style={{ justifyContent: "center", marginTop: 4 }}>
                  {status === "sending" ? "Sending…" : "Request My Demo"}
                </button>
                <p style={{ fontSize: 13, color: "var(--text-dim)", textAlign: "center" }}>No pressure, no spam. A real person will reach out.</p>
              </form>
            )}
          </motion.div>
        </div>
      </section>
    </>
  );
}
