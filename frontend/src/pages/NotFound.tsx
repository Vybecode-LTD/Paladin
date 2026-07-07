import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Compass } from "lucide-react";

const fadeUp = {
  initial: { opacity: 0, y: 24 }, whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-80px" }, transition: { duration: 0.5 },
};

export default function NotFound() {
  return (
    <section className="container" style={{ padding: "140px 0 120px", textAlign: "center" }}>
      <motion.div {...fadeUp} style={{ maxWidth: 560, margin: "0 auto" }}>
        <div className="glyph-badge glyph-blue" style={{ margin: "0 auto 16px" }}>
          <Compass size={22} />
        </div>
        <span className="eyebrow">404</span>
        <h1 style={{ fontSize: "clamp(32px, 5vw, 48px)", fontWeight: 800, letterSpacing: "-0.03em", margin: "16px 0 20px" }}>
          This page took a <span className="gradient-text">wrong turn.</span>
        </h1>
        <p style={{ fontSize: 17, color: "var(--text-muted)", marginBottom: 32 }}>
          We couldn't find what you're looking for. It may have moved, or the link
          might be off — either way, let's get you back on track.
        </p>
        <Link to="/" className="btn btn-primary">Back to Home <ArrowRight size={18} /></Link>
      </motion.div>
    </section>
  );
}
