import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, ClipboardList, PhoneCall, Activity, Send, ShieldCheck } from "lucide-react";
import Seo from "@/components/Seo";

const fadeUp = {
  initial: { opacity: 0, y: 24 }, whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-80px" }, transition: { duration: 0.5 },
};

const steps = [
  { icon: ClipboardList, glyph: "blue", n: "01", title: "Prepare", body: "Load the candidate's materials into Paladin — LinkedIn URL, résumé, job description. In seconds you get a pre-call skills-gap read that tells you exactly where to focus. Optional but powerful — even a cold call benefits from live prompts and context." },
  { icon: PhoneCall, glyph: "violet", n: "02", title: "Connect", body: "Paladin rings your phone first. You answer, and it dials the candidate and bridges the call. To the candidate, it's a normal phone call from you — because it is. Nothing to install, nothing to explain." },
  { icon: Activity, glyph: "cyan", n: "03", title: "Intelligence", body: "As you talk, Paladin listens to both sides and feeds the Intelligence Pane on your screen: a live transcript, timed follow-up prompts, on-the-fly definitions for technical terms, and markers on moments worth revisiting. You glance, you steer, you stay fully present in the conversation." },
  { icon: Send, glyph: "coral", n: "04", title: "Deliver", body: "The moment you hang up, Paladin generates a client-ready summary — key points, skills-match confidence, culture-fit read — ready to forward to your hiring manager or client. The call is captured while it's fresh, without you writing a word." },
];

export default function HowItWorks() {
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
        <motion.div {...fadeUp} style={{ maxWidth: 720 }}>
          <span className="eyebrow">How It Works</span>
          <h1 style={{ fontSize: "clamp(36px, 6vw, 60px)", fontWeight: 800, letterSpacing: "-0.03em", margin: "16px 0 20px" }}>
            Four steps. One live call. <span className="gradient-text">Zero friction.</span>
          </h1>
          <p style={{ fontSize: 19, color: "var(--text-muted)" }}>
            Paladin fits the way you already recruit. No new dialer, no app for the
            candidate, no change to your workflow — just better information, in the moment.
          </p>
        </motion.div>
      </section>

      <section className="section container">
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {steps.map((s, i) => (
            <motion.div key={s.n} {...fadeUp} transition={{ duration: 0.5, delay: i * 0.06 }} className="card"
              style={{ display: "grid", gridTemplateColumns: "auto auto 1fr", gap: 24, alignItems: "center" }}>
              <div className="gradient-text" style={{ fontSize: 40, fontWeight: 800, fontFamily: "var(--font-mono)", opacity: 0.5 }}>{s.n}</div>
              <div className={`glyph-badge glyph-${s.glyph}`} style={{ width: 52, height: 52 }}>
                <s.icon size={24} color="currentColor" aria-hidden="true" />
              </div>
              <div>
                <h3 style={{ fontSize: 21, fontWeight: 700, marginBottom: 8 }}>{s.title}</h3>
                <p style={{ color: "var(--text-muted)", fontSize: 16 }}>{s.body}</p>
              </div>
            </motion.div>
          ))}
        </div>
        <motion.div {...fadeUp} style={{ marginTop: 48, padding: 28, textAlign: "center", borderRadius: "var(--radius)", border: "1px dashed var(--border-bright)" }}>
          <p style={{ color: "var(--text-muted)", fontSize: 16 }}>
            <strong style={{ color: "var(--text)" }}>What you need:</strong> your existing phone. That's the whole list.
          </p>
        </motion.div>

        <motion.div {...fadeUp} className="card" style={{ marginTop: 24, display: "grid", gridTemplateColumns: "auto 1fr", gap: 24, alignItems: "center" }}>
          <div className="glyph-badge glyph-violet" style={{ width: 52, height: 52 }}>
            <ShieldCheck size={24} color="currentColor" aria-hidden="true" />
          </div>
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
          <Link to="/contact" className="btn btn-primary">Request a Demo <ArrowRight size={18} /></Link>
        </motion.div>
      </section>
    </>
  );
}
