import { useRef, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion, useInView } from "framer-motion";
import { ArrowRight, Brain, Radio, BookOpen, FileCheck, Layers } from "lucide-react";
import Seo from "@/components/Seo";
import TextScrim from "@/components/TextScrim";
import { useFadeUp } from "@/hooks/useReveal";

const features = [
  {
    id: "skills-gap", icon: Brain, glyph: "blue",
    title: "Pre-Call Skills Gap Analysis",
    body: "Feed Paladin a LinkedIn URL, the résumé, and the job description. Before you dial, it produces a structured read: where the candidate maps to the role, where the résumé is thin, and exactly what to probe. You start with a plan, not a cold read.",
    zoneLabel: "SKILLS GAP", zoneSample: "\"Yocto Project\" expertise — 92% role match",
  },
  {
    id: "live-prompts", icon: Radio, glyph: "violet",
    title: "Live Prompts",
    body: "As the conversation unfolds, Paladin pushes targeted, context-aware follow-up questions to your screen. Catch a glossed-over gap; go deeper when it counts. The prompts are a co-pilot, not an autopilot — you stay in control.",
    zoneLabel: "LIVE PROMPT", zoneSample: "💡 Ask which services were migrated first",
  },
  {
    id: "context", icon: BookOpen, glyph: "cyan",
    title: "Real-Time Context",
    body: "When a candidate drops a framework, tool, or acronym you don't know, Paladin defines it on-screen in plain language, instantly. Interview senior candidates in unfamiliar domains with confidence — and ask the sharper second question.",
    zoneLabel: "CONTEXT", zoneSample: "\"Yocto\" = an embedded-Linux build system",
  },
  {
    id: "summary", icon: FileCheck, glyph: "coral",
    title: "Post-Call Summary",
    body: "Seconds after you hang up, Paladin delivers a client-ready summary: key takeaways, a skills-match confidence score, and a culture-fit read. Send it straight to your hiring manager — no scramble to reconstruct the call from memory.",
    zoneLabel: "SUMMARY", zoneSample: "Fit 91% · Culture 84% · Report ready",
  },
];

function IntelligencePaneMock({ activeId }: { activeId: string }) {
  return (
    <div style={{
      borderRadius: "var(--radius-lg)", overflow: "hidden",
      background: "var(--console-bg)", backdropFilter: "blur(20px)", WebkitBackdropFilter: "blur(20px)",
      boxShadow: "var(--shadow-depth-3)",
    }}>
      <div className="signal-trace" style={{ height: 2, borderRadius: 0 }} />
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "14px 20px", borderBottom: "1px solid var(--console-border)" }}>
        <span className="live-dot" style={{ width: 7, height: 7, borderRadius: 99, background: "var(--console-glyph-cyan)", color: "var(--console-glyph-cyan)" }} />
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--console-text)" }}>The Intelligence Pane</span>
      </div>
      {features.map((f) => {
        const active = f.id === activeId;
        return (
          <div key={f.id} style={{
            padding: "18px 20px",
            borderBottom: "1px solid var(--console-border)",
            borderLeft: `3px solid ${active ? `var(--console-glyph-${f.glyph})` : "transparent"}`,
            background: active ? `color-mix(in srgb, var(--console-glyph-${f.glyph}) 12%, transparent)` : "transparent",
            transition: "background 0.35s ease, border-color 0.35s ease",
          }}>
            <div style={{
              fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.08em",
              color: active ? `var(--console-glyph-${f.glyph})` : "var(--console-text-dim)",
              transition: "color 0.35s ease",
            }}>
              {f.zoneLabel}
            </div>
            <div style={{ fontSize: 14, color: "var(--console-text)", marginTop: 6, opacity: active ? 1 : 0.55, transition: "opacity 0.35s ease" }}>
              {f.zoneSample}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function FeatureBlock({ f, onActive }: { f: typeof features[number]; onActive: (id: string) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { margin: "-40% 0px -40% 0px" });

  useEffect(() => {
    if (inView) onActive(f.id);
  }, [inView, f.id, onActive]);

  return (
    <div ref={ref} style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: 20, alignItems: "start", padding: "28px 0", borderBottom: "1px solid var(--border)" }}>
      <div className={`glyph-badge glyph-${f.glyph}`} style={{ width: 48, height: 48, marginBottom: 0 }}>
        <f.icon size={22} color="currentColor" aria-hidden="true" />
      </div>
      <div>
        <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>{f.title}</h3>
        <p style={{ color: "var(--text-muted)", fontSize: 16 }}>{f.body}</p>
      </div>
    </div>
  );
}

export default function Product() {
  const fadeUp = useFadeUp();
  const [activeId, setActiveId] = useState(features[0].id);

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
        <TextScrim style={{ maxWidth: 760 }}>
          <motion.div {...fadeUp}>
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
        </TextScrim>
      </section>

      {/* The Intelligence Pane — one persistent panel, annotated live as you scroll */}
      <section className="section" style={{ background: "var(--bg-elevated)", borderBlock: "1px solid var(--border)" }}>
        <div className="container">
          <motion.div {...fadeUp} style={{ maxWidth: 640, marginBottom: 48 }}>
            <div className="glyph-badge glyph-amber" style={{ display: "inline-grid", width: 50, height: 50 }}>
              <Layers size={24} color="currentColor" aria-hidden="true" />
            </div>
            <h2 className="section-title" style={{ marginTop: 18 }}>The Intelligence Pane</h2>
            <p style={{ color: "var(--text-muted)", marginTop: 16, fontSize: 17 }}>
              Everything Paladin surfaces appears in one calm, glanceable panel beside
              your call — never in your ear, never interrupting your flow. Scroll to see
              each piece light up.
            </p>
          </motion.div>

          <div className="sticky-pane-row">
            <div>
              {features.map((f) => (
                <FeatureBlock key={f.id} f={f} onActive={setActiveId} />
              ))}
            </div>
            <div style={{ position: "sticky", top: 100 }}>
              <IntelligencePaneMock activeId={activeId} />
            </div>
          </div>
        </div>
      </section>

      <section className="container" style={{ paddingBottom: 40 }}>
        <motion.div {...fadeUp} className="card-deep" style={{ textAlign: "center" }}>
          <h2 className="section-title">The best way to understand Paladin is to watch it work.</h2>
          <Link to="/contact" className="btn btn-primary" style={{ marginTop: 24 }}>Request a Demo <ArrowRight size={18} aria-hidden="true" /></Link>
        </motion.div>
      </section>
    </>
  );
}
