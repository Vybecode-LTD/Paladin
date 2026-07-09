import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight, Radio, Brain, BookOpen, FileCheck, Phone, XCircle, CheckCircle2,
} from "lucide-react";
import Seo from "@/components/Seo";
import ProductScreenshot from "@/components/ProductScreenshot";
import LiveCallDemo from "@/components/LiveCallDemo";

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-80px" },
  transition: { duration: 0.5 },
};

const stats = [
  { n: "74%", label: "of résumés now contain AI-generated content", src: "Resume Genius, 2025" },
  { n: "34%", label: "of recruiter time spent filtering deceptive candidates", src: "iHire, 2025" },
  { n: "$17K", label: "average cost of a bad hire that fails within 90 days", src: "SHRM" },
  { n: "25%", label: "of candidate interactions may involve AI deception by 2028", src: "Projected" },
];

const pillars = [
  { icon: Brain, glyph: "blue", title: "Pre-Call Skills Gap", body: "Drop in a LinkedIn URL, résumé, and job description. Walk into the call already knowing where to dig." },
  { icon: Radio, glyph: "violet", title: "Live Prompts", body: "The right follow-up question appears on your screen the moment it becomes relevant." },
  { icon: BookOpen, glyph: "cyan", title: "Real-Time Context", body: "Unfamiliar tech or jargon is defined on-screen as the candidate says it. Never bluff a technical answer again." },
  { icon: FileCheck, glyph: "coral", title: "Post-Call Summary", body: "A client-ready write-up with skills-match and culture-fit confidence scores, seconds after you hang up." },
];

const compare = [
  ["ATS filters", "Before you talk", "Screen people out"],
  ["LinkedIn", "Static", "Show a profile"],
  ["HireVue", "After the call", "Record for later review"],
  ["Chatbots", "Instead of you", "Remove the human"],
];

export default function Home() {
  return (
    <>
      <Seo
        title="Paladin — Real-Time AI Intelligence for Recruiting Calls | Ashford & Briggs"
        description="Paladin gives recruiters live intelligence during candidate calls — skills gaps, decoded jargon, the right question at the right moment. No app required."
        path="/"
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          name: "Paladin",
          url: "https://ashfordbriggs.com",
          description:
            "Real-time AI intelligence for recruiter phone calls. Paladin surfaces skills gaps, decodes jargon, and delivers live prompts during the call, then produces a post-call summary — all through the recruiter's existing phone, no app required.",
          applicationCategory: "BusinessApplication",
          operatingSystem: "Any",
          publisher: {
            "@type": "Organization",
            name: "Ashford & Briggs",
            url: "https://ashfordbriggs.com",
          },
        }}
      />
      {/* HERO */}
      <section style={{ position: "relative", padding: "100px 0 90px", overflow: "hidden" }}>
        <div style={{
          position: "absolute", top: "-20%", right: "-10%",
          width: 900, height: 600,
          background: "radial-gradient(ellipse, var(--accent-glow), transparent 70%)",
          filter: "blur(60px)", opacity: 0.5, pointerEvents: "none",
        }} />
        <div className="container" style={{ position: "relative" }}>
          <motion.div {...fadeUp} transition={{ duration: 0.5 }}
            style={{ display: "block", width: "100%", textAlign: "center", marginBottom: 20 }}>
            <span className="blue-gradient-text" style={{ display: "inline-block", fontWeight: 700, fontSize: "clamp(26px, 3.2vw, 30px)", letterSpacing: "0.01em" }}>
              Real-time AI Intelligence for Recruiting Calls
            </span>
          </motion.div>
          <div className="split-row" style={{ alignItems: "stretch" }}>
            <div>
              <motion.h1 {...fadeUp} transition={{ duration: 0.5, delay: 0.05 }}
                style={{ fontWeight: 800, letterSpacing: "-0.03em", lineHeight: 1.05, margin: "22px 0" }}>
                <span style={{ display: "block", fontSize: "clamp(26px, 3.4vw, 40px)" }}>
                  Recruiters need<br />superhuman abilities.
                </span>
                <span style={{ display: "block", fontSize: "clamp(32px, 4.4vw, 50px)", color: "var(--accent)", marginTop: "0.25em" }}>
                  Meet Paladin
                </span>
              </motion.h1>
              <motion.p {...fadeUp} transition={{ duration: 0.5, delay: 0.1 }}
                style={{ fontSize: "clamp(15px, 1.6vw, 18px)", color: "var(--text-muted)", maxWidth: 520, margin: "0 0 34px" }}>
                Paladin researches the job, briefs you on the candidate, and coaches
                you on the live call — on the phone you already use, no app required.
                In a world racing to replace human interaction with AI, Paladin
                strengthens the human relationship that recruiting was built on.
              </motion.p>
              <motion.div {...fadeUp} transition={{ duration: 0.5, delay: 0.15 }}
                style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
                <Link to="/contact" className="btn btn-primary">Request a Demo <ArrowRight size={18} /></Link>
                <Link to="/how-it-works" className="btn btn-ghost">See how it works</Link>
              </motion.div>
              <motion.p {...fadeUp} transition={{ duration: 0.5, delay: 0.2 }}
                style={{ marginTop: 22, fontSize: 14, color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                Built by recruiters, in Jacksonville, FL.
              </motion.p>
            </div>
            <motion.div {...fadeUp} transition={{ duration: 0.6, delay: 0.2 }}
              style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <ProductScreenshot
                priority
                src="/images/product-candidate-profile.png"
                alt="Paladin candidate profile showing contact details, fit score, and linked opportunities"
                style={{ width: "112.5%", flexShrink: 0 }}
              />
            </motion.div>
          </div>
        </div>
      </section>

      {/* LIVE CALL DEMO */}
      <section className="container" style={{ paddingBottom: 40 }}>
        <motion.div {...fadeUp} transition={{ duration: 0.6, delay: 0.1 }} style={{ maxWidth: 900, margin: "0 auto" }}>
          <LiveCallDemo />
        </motion.div>
      </section>

      {/* PROBLEM */}
      <section className="section container">
        <motion.div {...fadeUp} style={{ textAlign: "center", maxWidth: 680, margin: "0 auto 56px" }}>
          <h2 className="section-title">Recruiting is drowning in AI-generated noise.</h2>
          <p style={{ color: "var(--text-muted)", marginTop: 16, fontSize: 18 }}>
            The résumé is no longer a reliable signal. The phone call is — if you can
            hear what matters in real time.
          </p>
        </motion.div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 20 }}>
          {stats.map((s, i) => (
            <motion.div key={s.n} {...fadeUp} transition={{ duration: 0.5, delay: i * 0.06 }} className="card">
              <div className="gradient-text" style={{ fontSize: 44, fontWeight: 800, letterSpacing: "-0.02em" }}>{s.n}</div>
              <p style={{ color: "var(--text-muted)", marginTop: 8, fontSize: 15 }}>{s.label}</p>
              <p style={{ color: "var(--text-dim)", marginTop: 10, fontSize: 12, fontFamily: "var(--font-mono)" }}>{s.src}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* PRODUCT PILLARS */}
      <section className="section" style={{ background: "var(--bg-elevated)", borderBlock: "1px solid var(--border)" }}>
        <div className="container">
          <motion.div {...fadeUp} style={{ textAlign: "center", maxWidth: 640, margin: "0 auto 56px" }}>
            <span className="eyebrow" style={{ fontSize: 26, fontWeight: 700 }}>Paladin</span>
            <h2 className="section-title" style={{ marginTop: 12, whiteSpace: "nowrap" }}>Real-time interview intelligence.</h2>
          </motion.div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 20 }}>
            {pillars.map((p, i) => (
              <motion.div key={p.title} {...fadeUp} transition={{ duration: 0.5, delay: i * 0.06 }} className="card">
                <div className={`glyph-badge glyph-${p.glyph}`}>
                  <p.icon size={22} color="currentColor" />
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>{p.title}</h3>
                <p style={{ color: "var(--text-muted)", fontSize: 15 }}>{p.body}</p>
              </motion.div>
            ))}
          </div>
          <motion.div {...fadeUp} style={{ textAlign: "center", marginTop: 40 }}>
            <Link to="/product" className="btn btn-ghost">Explore Paladin <ArrowRight size={16} /></Link>
          </motion.div>
        </div>
      </section>

      {/* DIFFERENTIATION */}
      <section className="section container">
        <motion.div {...fadeUp} style={{ textAlign: "center", maxWidth: 720, margin: "0 auto 48px" }}>
          <span className="eyebrow" style={{ fontSize: 26, fontWeight: 700 }}>Paladin vs. the alternatives</span>
          <h2 className="section-title" style={{ marginTop: 12 }}>
            <span style={{ whiteSpace: "nowrap", fontSize: "clamp(21px, 3vw, 33px)" }}>Do other products work in real-time? No.</span><br />
            <span className="gradient-text">Paladin does.</span>
          </h2>
        </motion.div>
        <motion.div {...fadeUp} className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 15 }}>
            <thead>
              <tr style={{ background: "var(--bg-elevated)", textAlign: "left" }}>
                <th style={{ padding: "16px 8px 16px 24px", width: 1 }}></th>
                <th style={{ padding: "16px 20px", color: "var(--text-dim)", fontWeight: 600 }}>Product</th>
                <th style={{ padding: "16px 20px", color: "var(--text-dim)", fontWeight: 600 }}>When it works</th>
                <th style={{ padding: "16px 20px", color: "var(--text-dim)", fontWeight: 600 }}>What it does</th>
              </tr>
            </thead>
            <tbody>
              {compare.map((row) => (
                <tr key={row[0]} style={{ borderTop: "1px solid var(--border)" }}>
                  <td style={{ padding: "16px 8px 16px 24px" }}>
                    <XCircle size={18} color="var(--danger)" />
                  </td>
                  <td style={{ padding: "16px 20px", color: "var(--text-muted)", fontWeight: 600 }}>{row[0]}</td>
                  <td style={{ padding: "16px 20px", color: "var(--text-muted)" }}>{row[1]}</td>
                  <td style={{ padding: "16px 20px", color: "var(--text-muted)" }}>{row[2]}</td>
                </tr>
              ))}
              <tr style={{ borderTop: "2px solid var(--accent)", background: "var(--accent-glow)" }}>
                <td style={{ padding: "18px 8px 18px 24px" }}>
                  <CheckCircle2 size={18} color="var(--accent)" />
                </td>
                <td style={{ padding: "18px 20px", fontWeight: 800 }}>Paladin</td>
                <td style={{ padding: "18px 20px", fontWeight: 700 }} className="gradient-text">Live, on the call</td>
                <td style={{ padding: "18px 20px", fontWeight: 700 }}>Make you sharper, in the moment</td>
              </tr>
            </tbody>
          </table>
        </motion.div>
      </section>

      {/* CLOSING CTA */}
      <section className="container" style={{ paddingBottom: 40 }}>
        <motion.div {...fadeUp} className="card" style={{
          textAlign: "center", padding: "64px 32px",
          background: "linear-gradient(140deg, var(--bg-card), rgba(30,111,212,0.12))",
          borderColor: "var(--border-bright)",
        }}>
          <div style={{ display: "inline-grid", placeItems: "center", width: 56, height: 56, borderRadius: 14, background: "var(--accent-glow)", marginBottom: 20 }}>
            <Phone size={26} color="var(--accent-bright)" />
          </div>
          <h2 className="section-title">See Paladin on a live call.</h2>
          <p style={{ color: "var(--text-muted)", maxWidth: 520, margin: "16px auto 28px", fontSize: 17 }}>
            A short demo is the fastest way to understand it. We'll show you the
            Intelligence Pane in action on a real recruiting scenario.
          </p>
          <Link to="/contact" className="btn btn-primary">Request a Demo <ArrowRight size={18} /></Link>
        </motion.div>
      </section>
    </>
  );
}
