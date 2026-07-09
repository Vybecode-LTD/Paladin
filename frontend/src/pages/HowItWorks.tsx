import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, ClipboardList, PhoneCall, Activity, Send } from "lucide-react";
import Seo from "@/components/Seo";
import ProductScreenshot from "@/components/ProductScreenshot";
import SignalLine from "@/components/SignalLine";
import Waveform from "@/components/Waveform";
import Brandmark from "@/components/Brandmark";
import TextScrim from "@/components/TextScrim";
import { useFadeUp } from "@/hooks/useReveal";

const steps = [
  {
    n: "01", icon: ClipboardList, glyph: "blue", title: "Prepare",
    eyebrow: "Step 01 — Prepare",
    heading: "Every candidate, one searchable list.",
    body: "Load LinkedIn, résumé, and job description in — Paladin hands back a pre-call skills-gap read before you dial. Optional, but even a cold call benefits from live prompts and context.",
    shot: { src: "/images/product-candidates-list.png", alt: "Paladin candidates list with search, status filter, and each candidate's linked opportunities and fit score" },
  },
  {
    n: "02", icon: PhoneCall, glyph: "violet", title: "Connect",
    eyebrow: "Step 02 — Connect",
    heading: "Paladin rings you first, then bridges the call.",
    body: "You answer, and it dials the candidate and connects the two of you. To the candidate, it's a normal call from you — because it is. Nothing to install, nothing to explain.",
  },
  {
    n: "03", icon: Activity, glyph: "cyan", title: "Intelligence",
    eyebrow: "Step 03 — Intelligence",
    heading: "Strengths and red flags, surfaced while you're still on the call.",
    body: "Paladin weighs what the candidate says against the role in real time — flagging gaps like a geographic mismatch and handing you the exact probing question to ask next.",
    shot: { src: "/images/product-analysis-pane.png", alt: "Paladin analysis pane showing candidate strengths, a regulatory-experience flag, and a geographic-mismatch red flag with a suggested probing question" },
  },
  {
    n: "04", icon: Send, glyph: "coral", title: "Deliver",
    eyebrow: "Step 04 — Deliver",
    heading: "A fit score and report, ready the moment you hang up.",
    body: "Every call rolls up into a fitment report with a confidence score — logged against the opportunity, ready to forward to your hiring manager.",
    shot: { src: "/images/product-reports.png", alt: "Paladin opportunity report view showing a 91% fit score, AI confidence rating, and generated fitment analysis reports" },
  },
];

function ConnectVisual() {
  return (
    <div style={{
      position: "relative", borderRadius: "var(--radius-lg)", overflow: "hidden",
      background: "var(--console-bg)", backdropFilter: "blur(20px)", WebkitBackdropFilter: "blur(20px)",
      boxShadow: "var(--shadow-depth-3)", padding: "48px 32px", textAlign: "center",
    }}>
      <div className="signal-trace" style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, borderRadius: 0 }} />
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 20 }}>
        <Brandmark size={44} />
        <Waveform bars={8} />
        <div style={{ width: 40, height: 40, borderRadius: 99, background: "var(--console-glyph-violet)", display: "grid", placeItems: "center", flexShrink: 0 }}>
          <PhoneCall size={18} color="var(--console-bg)" aria-hidden="true" />
        </div>
      </div>
      <p style={{ marginTop: 24, color: "var(--console-text)", fontSize: 15, maxWidth: 380, marginInline: "auto" }}>
        Paladin rings you first, then dials and bridges the candidate — a normal call, from your number.
      </p>
    </div>
  );
}

export default function HowItWorks() {
  const fadeUp = useFadeUp();

  return (
    <>
      <Seo
        title="How Paladin Works | Ashford & Briggs"
        description="How Paladin works: a pre-call skills-gap read, a normal phone call, live in-call intelligence, and a client-ready summary the moment you hang up."
        path="/how-it-works"
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "HowTo",
          name: "How Paladin Works",
          description: "How recruiters use Paladin for real-time AI intelligence on live candidate calls, through their existing phone.",
          step: steps.map((s) => ({
            "@type": "HowToStep",
            position: Number(s.n),
            name: s.title,
            text: s.body,
          })),
        }}
      />
      <section style={{ padding: "100px 0 40px" }} className="container">
        <TextScrim style={{ maxWidth: 720 }}>
          <motion.div {...fadeUp}>
            <span className="eyebrow">How It Works</span>
            <h1 style={{ fontSize: "clamp(36px, 6vw, 60px)", fontWeight: 800, letterSpacing: "-0.03em", margin: "16px 0 20px" }}>
              Four steps. One live call. <span className="gradient-text">Zero friction.</span>
            </h1>
            <p style={{ fontSize: 19, color: "var(--text-muted)" }}>
              Paladin fits the way you already recruit. No new dialer, no app for the
              candidate, no change to your workflow — just better information, in the moment.
            </p>
          </motion.div>
        </TextScrim>
      </section>

      {/* Compact at-a-glance strip — a real h2, not a repeated card list */}
      <section className="container" style={{ paddingBottom: 56 }}>
        <TextScrim style={{ display: "block", width: "fit-content" }} bleed={40}>
          <motion.h2 {...fadeUp} className="eyebrow" style={{ display: "block", marginBottom: 20 }}>The four steps, at a glance</motion.h2>
        </TextScrim>
        <SignalLine>
          {steps.map((s) => (
            <motion.div key={s.n} {...fadeUp} style={{ position: "relative", paddingLeft: 60, minHeight: 28, display: "flex", alignItems: "center" }}>
              <div style={{
                position: "absolute", left: 14, width: 28, height: 28, borderRadius: 99,
                background: "var(--bg)", border: `2px solid var(--glyph-${s.glyph})`,
                display: "grid", placeItems: "center",
              }}>
                <s.icon size={14} color={`var(--glyph-${s.glyph})`} aria-hidden="true" />
              </div>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--text-dim)", marginRight: 10 }}>{s.n}</span>
              <strong style={{ fontSize: 16 }}>{s.title}</strong>
            </motion.div>
          ))}
        </SignalLine>
      </section>

      {/* See it in action — the primary explanation, real screenshots */}
      <section className="section container" style={{ paddingTop: 0 }}>
        <TextScrim style={{ maxWidth: 640, margin: "0 auto 56px" }}>
          <motion.div {...fadeUp} style={{ textAlign: "center" }}>
            <span className="eyebrow">See It In Action</span>
            <h2 className="section-title" style={{ marginTop: 12 }}>From candidate list to client-ready report.</h2>
          </motion.div>
        </TextScrim>
        <div style={{ display: "flex", flexDirection: "column", gap: 80 }}>
          {steps.map((s, i) => (
            <div key={s.n} className={i % 2 === 1 ? "split-row reverse" : "split-row"}>
              <TextScrim>
                <motion.div {...fadeUp}>
                  <span className="eyebrow">{s.eyebrow}</span>
                  <h3 style={{ fontSize: 24, fontWeight: 700, margin: "10px 0" }}>{s.heading}</h3>
                  <p style={{ color: "var(--text-muted)", fontSize: 16 }}>{s.body}</p>
                </motion.div>
              </TextScrim>
              <motion.div {...fadeUp} transition={{ duration: 0.5, delay: 0.1 }}>
                {s.shot ? <ProductScreenshot src={s.shot.src} alt={s.shot.alt} /> : <ConnectVisual />}
              </motion.div>
            </div>
          ))}
        </div>
      </section>

      <section className="section container" style={{ paddingTop: 0 }}>
        <TextScrim>
          <motion.div {...fadeUp} style={{ padding: 28, textAlign: "center", borderRadius: "var(--radius)", border: "1px dashed var(--border-bright)" }}>
            <p style={{ color: "var(--text-muted)", fontSize: 16 }}>
              <strong style={{ color: "var(--text)" }}>What you need:</strong> your existing phone. That's the whole list.
            </p>
          </motion.div>
        </TextScrim>

        <motion.div {...fadeUp} className="card" style={{ marginTop: 24, display: "grid", gridTemplateColumns: "auto 1fr", gap: 24, alignItems: "center" }}>
          <Brandmark size={44} />
          <div>
            <h3 style={{ fontSize: 21, fontWeight: 700, marginBottom: 8 }}>Security &amp; the human-first promise</h3>
            <p style={{ color: "var(--text-muted)", fontSize: 16 }}>
              Paladin is designed to strengthen the recruiter–candidate relationship, not
              surveil it. It's a tool that makes a human better at a human job.{" "}
              <Link to="/about" style={{ color: "var(--text)", textDecoration: "underline" }}>More in About</Link>.
            </p>
          </div>
        </motion.div>
      </section>

      <section className="container" style={{ paddingBottom: 40 }}>
        <motion.div {...fadeUp} style={{ textAlign: "center" }}>
          <Link to="/contact" className="btn btn-primary">Request a Demo <ArrowRight size={18} aria-hidden="true" /></Link>
        </motion.div>
      </section>
    </>
  );
}
