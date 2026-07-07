import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, MapPin } from "lucide-react";

const fadeUp = {
  initial: { opacity: 0, y: 24 }, whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-80px" }, transition: { duration: 0.5 },
};

export default function About() {
  return (
    <>
      <section style={{ padding: "100px 0 60px" }} className="container">
        <motion.div {...fadeUp} style={{ maxWidth: 760 }}>
          <span className="eyebrow">About</span>
          <h1 style={{ fontSize: "clamp(36px, 6vw, 60px)", fontWeight: 800, letterSpacing: "-0.03em", margin: "16px 0 20px" }}>
            We're betting on the <span className="gradient-text">human conversation.</span>
          </h1>
          <p style={{ fontSize: 19, color: "var(--text-muted)" }}>
            Ashford & Briggs builds tools that make recruiters sharper — not obsolete.
            Paladin is our first.
          </p>
        </motion.div>
      </section>

      <section className="section container" style={{ maxWidth: 820 }}>
        <motion.div {...fadeUp}>
          <h2 className="section-title" style={{ marginBottom: 20 }}>The story</h2>
          <p style={{ color: "var(--text-muted)", fontSize: 17, marginBottom: 18 }}>
            Recruiting changed the day generative AI put a polished résumé within
            everyone's reach. Overnight, the document recruiters had relied on for
            decades stopped being a trustworthy signal. The industry's response was to
            add more automation — more filters, more async screens, more ways to avoid
            talking to people.
          </p>
          <p style={{ color: "var(--text-muted)", fontSize: 17, marginBottom: 18 }}>
            We think that's backwards. When every written signal can be faked, the live
            conversation becomes <em>more</em> valuable, not less. So we built Paladin to
            make that conversation as sharp as it can possibly be: real-time intelligence
            that rides along on the call and hands the recruiter better information at
            exactly the moment they need it.
          </p>
        </motion.div>

        <motion.div {...fadeUp} className="card" style={{ marginTop: 32, background: "linear-gradient(140deg, var(--bg-card), rgba(0,118,209,0.1))" }}>
          <h3 style={{ fontSize: 15, color: "var(--accent-bright)", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 10 }}>Mission</h3>
          <p style={{ fontSize: 20, fontWeight: 600 }}>To keep the human at the center of hiring — and give that human superpowers.</p>
        </motion.div>

        <motion.div {...fadeUp} style={{ marginTop: 32, display: "flex", alignItems: "center", gap: 10, color: "var(--text-muted)" }}>
          <MapPin size={18} color="var(--accent-bright)" />
          <span>Jacksonville, Florida · Founded 2026 · A small team that ships.</span>
        </motion.div>
      </section>

      <section className="section" style={{ background: "var(--bg-elevated)", borderBlock: "1px solid var(--border)" }}>
        <div className="container">
          <motion.h2 {...fadeUp} className="section-title" style={{ textAlign: "center", marginBottom: 48 }}>Founders</motion.h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, maxWidth: 900, margin: "0 auto" }}>
            <motion.div {...fadeUp} className="card">
              <h3 style={{ fontSize: 22, fontWeight: 700 }}>John Evans</h3>
              <p style={{ color: "var(--accent-bright)", fontFamily: "var(--font-mono)", fontSize: 13, margin: "4px 0 14px" }}>CO-FOUNDER</p>
              <p style={{ color: "var(--text-muted)", fontSize: 15 }}>
                Creator of Resumoose. Fullstack engineer with deep experience in AI
                systems — retrieval-augmented generation and context engineering. John
                builds the intelligence layer that makes Paladin feel like it's reading
                the room with you.
              </p>
            </motion.div>
            <motion.div {...fadeUp} transition={{ duration: 0.5, delay: 0.1 }} className="card">
              <h3 style={{ fontSize: 22, fontWeight: 700 }}>Matt Barker</h3>
              <p style={{ color: "var(--accent-bright)", fontFamily: "var(--font-mono)", fontSize: 13, margin: "4px 0 14px" }}>CO-FOUNDER</p>
              <p style={{ color: "var(--text-muted)", fontSize: 15 }}>
                Founder of 1-800-VET-INFO. Telephony and voice-infrastructure veteran.
                Matt owns the hard part everyone else avoids: making real-time call
                intelligence work reliably over an ordinary phone line, with nothing to
                install.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      <section className="container" style={{ padding: "80px 0 40px", textAlign: "center" }}>
        <motion.div {...fadeUp}>
          <h2 className="section-title" style={{ marginBottom: 24 }}>Want to see what we've built?</h2>
          <Link to="/contact" className="btn btn-primary">Request a Demo <ArrowRight size={18} /></Link>
        </motion.div>
      </section>
    </>
  );
}
