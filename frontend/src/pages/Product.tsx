import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Brain, Radio, BookOpen, FileCheck, Layers } from "lucide-react";
import Seo from "@/components/Seo";
import ProductScreenshot from "@/components/ProductScreenshot";

const fadeUp = {
  initial: { opacity: 0, y: 24 }, whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-80px" }, transition: { duration: 0.5 },
};

const features = [
  { icon: Brain, glyph: "blue", title: "Pre-Call Skills Gap Analysis", body: "Feed Paladin a LinkedIn URL, the résumé, and the job description. Before you dial, it produces a structured read: where the candidate maps to the role, where the résumé is thin, and exactly what to probe. You start with a plan, not a cold read." },
  { icon: Radio, glyph: "violet", title: "Live Prompts", body: "As the conversation unfolds, Paladin pushes targeted, context-aware follow-up questions to your screen. Catch a glossed-over gap; go deeper when it counts. The prompts are a co-pilot, not an autopilot — you stay in control." },
  { icon: BookOpen, glyph: "cyan", title: "Real-Time Context", body: "When a candidate drops a framework, tool, or acronym you don't know, Paladin defines it on-screen in plain language, instantly. Interview senior candidates in unfamiliar domains with confidence — and ask the sharper second question." },
  { icon: FileCheck, glyph: "coral", title: "Post-Call Summary", body: "Seconds after you hang up, Paladin delivers a client-ready summary: key takeaways, a skills-match confidence score, and a culture-fit read. Send it straight to your hiring manager — no scramble to reconstruct the call from memory." },
];

export default function Product() {
  return (
    <>
      <Seo
        title="Paladin — Real-Time AI Intelligence for Recruiting Calls | Ashford & Briggs"
        description="Paladin gives recruiters live intelligence during candidate calls: skills-gap analysis, real-time prompts, jargon context, and post-call summaries."
        path="/product"
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          name: "Paladin",
          applicationCategory: "BusinessApplication",
          operatingSystem: "Any (works through your existing phone, no app install required)",
          description:
            "Real-time AI intelligence for recruiting phone calls. Paladin listens to both sides of a live call and surfaces pre-call skills-gap analysis, live contextual prompts, on-call jargon definitions, and a post-call summary with a skills-match confidence score.",
          brand: {
            "@type": "Organization",
            name: "Ashford & Briggs",
          },
        }}
      />
      <section style={{ padding: "100px 0 60px" }} className="container">
        <motion.div {...fadeUp} style={{ maxWidth: 760 }}>
          <span className="eyebrow">The Product</span>
          <h1 style={{ fontSize: "clamp(38px, 6vw, 64px)", fontWeight: 800, letterSpacing: "-0.03em", margin: "16px 0 20px" }}>
            <span className="gradient-text">Paladin</span>
          </h1>
          <p style={{ fontSize: 20, color: "var(--text-muted)" }}>
            Real-time counter-intelligence for recruiting calls. It listens to both
            sides of the conversation and turns it into live, on-screen intelligence —
            so you lead the call instead of scrambling to keep up.
          </p>
        </motion.div>
      </section>

      {/* Intelligence Pane */}
      <section className="section" style={{ background: "var(--bg-elevated)", borderBlock: "1px solid var(--border)" }}>
        <div className="container split-row">
          <motion.div {...fadeUp}>
            <div className="glyph-badge glyph-amber" style={{ display: "inline-grid", width: 50, height: 50, marginBottom: 18 }}>
              <Layers size={24} color="currentColor" />
            </div>
            <h2 className="section-title">The Intelligence Pane</h2>
            <p style={{ color: "var(--text-muted)", marginTop: 16, fontSize: 17 }}>
              Everything Paladin surfaces appears in one calm, glanceable panel beside
              your call — never in your ear, never interrupting your flow. Strengths,
              red flags, and probing questions to ask, generated straight from the
              conversation.
            </p>
          </motion.div>
          <motion.div {...fadeUp} transition={{ duration: 0.5, delay: 0.1 }}>
            <ProductScreenshot
              src="/images/product-analysis-pane.png"
              alt="Paladin analysis pane showing candidate strengths, a low-risk regulatory flag, and a geographic-mismatch red flag with a suggested probing question"
            />
          </motion.div>
        </div>
      </section>

      {/* Feature deep-dives */}
      <section className="section container">
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {features.map((f, i) => (
            <motion.div key={f.title} {...fadeUp} transition={{ duration: 0.5, delay: i * 0.05 }} className="card"
              style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: 24, alignItems: "start" }}>
              <div className={`glyph-badge glyph-${f.glyph}`} style={{ width: 52, height: 52 }}>
                <f.icon size={24} color="currentColor" />
              </div>
              <div>
                <h3 style={{ fontSize: 21, fontWeight: 700, marginBottom: 10 }}>{f.title}</h3>
                <p style={{ color: "var(--text-muted)", fontSize: 16 }}>{f.body}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="container" style={{ paddingBottom: 40 }}>
        <motion.div {...fadeUp} className="card" style={{ textAlign: "center", padding: "56px 32px", background: "linear-gradient(140deg, var(--bg-card), rgba(30,111,212,0.12))" }}>
          <h2 className="section-title">The best way to understand Paladin is to watch it work.</h2>
          <Link to="/contact" className="btn btn-primary" style={{ marginTop: 24 }}>Request a Demo <ArrowRight size={18} /></Link>
        </motion.div>
      </section>
    </>
  );
}
