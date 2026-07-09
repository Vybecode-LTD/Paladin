import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, MapPin } from "lucide-react";
import Seo from "@/components/Seo";
import TextScrim from "@/components/TextScrim";
import { useFadeUp } from "@/hooks/useReveal";

const founders = [
  {
    name: "John Evans", variant: "intelligence", color: "var(--glyph-blue)",
    signal: "SIGNAL: INTELLIGENCE",
    bio: "Creator of Resumoose. Fullstack engineer with deep experience in AI systems — retrieval-augmented generation and context engineering. John builds the intelligence layer that makes Paladin feel like it's reading the room with you.",
  },
  {
    name: "Matt Barker", variant: "telephony", color: "var(--glyph-violet)",
    signal: "SIGNAL: TELEPHONY",
    bio: "Founder of 1-800-VET-INFO. Telephony and voice-infrastructure veteran. Matt owns the hard part everyone else avoids: making real-time call intelligence work reliably over an ordinary phone line, with nothing to install.",
  },
];

/** Per-founder mark — the same shield silhouette as Brandmark, cut with a
 * different negative-space pattern per specialty instead of a stock avatar. */
function FounderMark({ variant, color }: { variant: "telephony" | "intelligence"; color: string }) {
  const maskPath = variant === "telephony"
    ? "M15 30 H21 L24 22 L28 36 L31 26 L34 30 H49"
    : "M17 20 L28 20 L28 32 L40 32 L40 44";
  return (
    <svg width={44} height={44} viewBox="0 0 64 64" fill="none" aria-hidden="true">
      <defs>
        <mask id={`founder-mask-${variant}`}>
          <rect width="64" height="64" fill="#fff" />
          <path d={maskPath} stroke="#000" strokeWidth="3.4" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        </mask>
      </defs>
      <path
        d="M14 9 H50 C57 9 58 15 58 23 C58 36 51 47 32 59
           C13 47 6 36 6 23 C6 15 7 9 14 9 Z"
        fill={color}
        mask={`url(#founder-mask-${variant})`}
      />
    </svg>
  );
}

export default function About() {
  const fadeUp = useFadeUp();

  return (
    <>
      <Seo
        title="About | Ashford & Briggs"
        description="Ashford & Briggs builds Paladin, real-time AI intelligence for recruiter phone calls. Founded 2026 in Jacksonville, FL, by John Evans and Matt Barker."
        path="/about"
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "AboutPage",
          name: "About Ashford & Briggs",
          url: "https://ashfordbriggs.com/about",
          mainEntity: {
            "@type": "Organization",
            name: "Ashford & Briggs",
            foundingDate: "2026",
            foundingLocation: {
              "@type": "Place",
              name: "Jacksonville, FL",
            },
            founders: [
              { "@type": "Person", name: "John Evans" },
              { "@type": "Person", name: "Matt Barker" },
            ],
            makesOffer: {
              "@type": "Offer",
              itemOffered: {
                "@type": "SoftwareApplication",
                name: "Paladin",
              },
            },
          },
        }}
      />
      <section style={{ padding: "100px 0 60px" }} className="container">
        <TextScrim style={{ maxWidth: 760 }}>
          <motion.div {...fadeUp}>
            <span className="eyebrow">About</span>
            <h1 style={{ fontSize: "clamp(36px, 6vw, 60px)", fontWeight: 800, letterSpacing: "-0.03em", margin: "16px 0 20px" }}>
              We're betting on the <span className="gradient-text">human conversation.</span>
            </h1>
            <p style={{ fontSize: 19, color: "var(--text-muted)" }}>
              Ashford & Briggs builds tools that make recruiters sharper — not obsolete.
              Paladin is our first.
            </p>
          </motion.div>
        </TextScrim>
      </section>

      <section className="section container" style={{ maxWidth: 820 }}>
        <TextScrim>
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
        </TextScrim>

        <motion.div {...fadeUp} className="card card-glow" style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 15, color: "var(--accent-bright)", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 10 }}>Mission</h3>
          <p style={{ fontSize: 20, fontWeight: 600 }}>To keep the human at the center of hiring — and give that human superpowers.</p>
        </motion.div>

        <TextScrim style={{ marginTop: 32 }}>
          <motion.div {...fadeUp} style={{ display: "flex", alignItems: "center", gap: 10, color: "var(--text-muted)" }}>
            <MapPin size={18} color="var(--accent-bright)" aria-hidden="true" />
            <span>Jacksonville, Florida · Founded 2026 · A small team that ships.</span>
          </motion.div>
        </TextScrim>
      </section>

      <section className="section" style={{ background: "var(--bg-elevated)", borderBlock: "1px solid var(--border)" }}>
        <div className="container">
          <motion.h2 {...fadeUp} className="section-title" style={{ textAlign: "center", marginBottom: 48 }}>Founders</motion.h2>
          <div className="founders-grid" style={{ position: "relative", maxWidth: 900, margin: "0 auto" }}>
            <div className="signal-trace" style={{
              position: "absolute", top: "50%", left: "calc(50% - 12px)", width: 24, transform: "translateY(-50%) rotate(90deg)",
            }} />
            {founders.map((f, i) => (
              <motion.div key={f.name} {...fadeUp} transition={{ duration: 0.5, delay: i * 0.1 }} className="card"
                style={{ marginTop: i === 1 ? 28 : 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16 }}>
                  <FounderMark variant={f.variant as "telephony" | "intelligence"} color={f.color} />
                  <div>
                    <h3 style={{ fontSize: 20, fontWeight: 700 }}>{f.name}</h3>
                    <p style={{ color: f.color, fontFamily: "var(--font-mono)", fontSize: 12, letterSpacing: "0.04em", marginTop: 2 }}>{f.signal}</p>
                  </div>
                </div>
                <p style={{ color: "var(--text-muted)", fontSize: 15 }}>{f.bio}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="container" style={{ padding: "80px 0 40px", textAlign: "center" }}>
        <motion.div {...fadeUp}>
          <TextScrim style={{ display: "block", width: "fit-content", margin: "0 auto" }}>
            <h2 className="section-title" style={{ marginBottom: 24 }}>Want to see what we've built?</h2>
          </TextScrim>
          <Link to="/contact" className="btn btn-primary">Request a Demo <ArrowRight size={18} aria-hidden="true" /></Link>
        </motion.div>
      </section>
    </>
  );
}
