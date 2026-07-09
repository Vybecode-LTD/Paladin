import { useState } from "react";
import { Outlet, Link, NavLink, useLocation } from "react-router-dom";
import {
  motion, AnimatePresence, useScroll, useTransform, useMotionValueEvent, useReducedMotion,
} from "framer-motion";
import FlowBackground from "@/components/FlowBackground";
import Brandmark from "@/components/Brandmark";
import Waveform from "@/components/Waveform";
import TextScrim from "@/components/TextScrim";

const nav = [
  { to: "/product", label: "Product" },
  { to: "/how-it-works", label: "How It Works" },
  { to: "/about", label: "About" },
  { to: "/blog", label: "Blog" },
];

function Header() {
  const { scrollY } = useScroll();
  const reduceMotion = useReducedMotion();
  const [hidden, setHidden] = useState(false);

  const headerBg = useTransform(scrollY, [0, 120], ["rgba(255,255,255,0.4)", "rgba(255,255,255,0.78)"]);
  const blurPx = useTransform(scrollY, [0, 120], [10, 20]);
  const backdropFilter = useTransform(blurPx, (v) => `blur(${v}px) saturate(160%)`);
  const shadowAlpha = useTransform(scrollY, [0, 120], [0.02, 0.08]);
  const boxShadow = useTransform(shadowAlpha, (v) => `0 1px 2px rgba(16,24,40,${v}), 0 4px 10px rgba(16,24,40,${v * 1.5})`);

  useMotionValueEvent(scrollY, "change", (latest) => {
    if (reduceMotion) return;
    const prev = scrollY.getPrevious() ?? latest;
    const diff = latest - prev;
    if (latest > 160 && diff > 0) setHidden(true);
    else if (diff < 0) setHidden(false);
  });

  return (
    <motion.header
      animate={{ y: hidden ? -80 : 0 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      style={{
        position: "sticky", top: 0, zIndex: 50,
        background: headerBg,
        backdropFilter, WebkitBackdropFilter: backdropFilter,
        borderBottom: "1px solid var(--glass-border)",
        boxShadow,
      }}
    >
      <div className="container" style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        height: 68,
      }}>
        <Link to="/" style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 700 }}>
          <Brandmark size={26} />
          <span>Ashford&nbsp;&&nbsp;Briggs</span>
        </Link>
        <nav style={{ display: "flex", gap: 28, alignItems: "center" }}>
          {nav.map((n) => (
            <NavLink key={n.to} to={n.to} className="nav-link">
              {({ isActive }) => (
                <span style={{ position: "relative", display: "inline-block", color: isActive ? "var(--accent-bright)" : "var(--text-muted)", fontSize: 15, fontWeight: 500 }}>
                  {n.label}
                  {isActive && (
                    <motion.span
                      layoutId="nav-active-indicator"
                      transition={{ type: "spring", stiffness: 380, damping: 32 }}
                      style={{
                        position: "absolute", left: 0, right: 0, bottom: -8, height: 2, borderRadius: 2,
                        background: "var(--accent)", boxShadow: "0 0 6px var(--accent-glow)",
                      }}
                    />
                  )}
                </span>
              )}
            </NavLink>
          ))}
          <motion.div
            animate={reduceMotion ? undefined : {
              boxShadow: [
                "0 4px 20px rgba(0,118,209,0.16)",
                "0 4px 28px rgba(0,118,209,0.34)",
                "0 4px 20px rgba(0,118,209,0.16)",
              ],
            }}
            transition={{ duration: 3, repeat: Infinity, repeatType: "mirror", ease: "easeInOut" }}
            style={{ borderRadius: "var(--radius)" }}
          >
            <Link to="/contact" className="btn btn-primary" style={{ padding: "9px 18px" }}>
              Request a Demo
            </Link>
          </motion.div>
        </nav>
      </div>
    </motion.header>
  );
}

/** A thin gradient bar that sweeps in on every route change — the "tuning
 * into a new signal" beat that stands in for a generic page-fade. */
function SignalWipe() {
  const location = useLocation();
  const reduceMotion = useReducedMotion();
  if (reduceMotion) return null;
  return (
    <motion.div
      key={location.pathname}
      initial={{ scaleX: 0, opacity: 1 }}
      animate={{ scaleX: 1, opacity: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      aria-hidden="true"
      style={{
        position: "fixed", top: 0, left: 0, right: 0, height: 3, zIndex: 100,
        transformOrigin: "left", pointerEvents: "none",
        background: "linear-gradient(90deg, var(--glyph-coral), var(--accent), var(--glyph-cyan))",
      }}
    />
  );
}

export default function PublicLayout() {
  const location = useLocation();
  const reduceMotion = useReducedMotion();

  return (
    <>
      <FlowBackground />
      <SignalWipe />
      <Header />

      <AnimatePresence mode="wait">
        <motion.main
          key={location.pathname}
          initial={reduceMotion ? { opacity: 1 } : { opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={reduceMotion ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: reduceMotion ? 0 : 0.2 }}
        >
          <Outlet />
        </motion.main>
      </AnimatePresence>

      <footer style={{ position: "relative", padding: "56px 0 40px", marginTop: 80 }}>
        <div className="container">
          <div className="signal-trace" style={{ marginBottom: 56 }} />
        </div>
        <div className="container" style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 40 }}>
          <TextScrim>
            <div style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 700, marginBottom: 12 }}>
              <Brandmark size={22} />
              Ashford & Briggs
            </div>
            <p style={{ color: "var(--text-dim)", fontSize: 14, maxWidth: 320, marginBottom: 16 }}>
              Real-time AI intelligence for recruiting calls. Built by recruiters in
              Jacksonville, FL.
            </p>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <Waveform size="thin" bars={8} />
              <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--text-dim)", letterSpacing: "0.04em" }}>
                MEET PALADIN
              </span>
            </div>
          </TextScrim>
          <TextScrim>
            <h4 style={{ fontSize: 13, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: 14, letterSpacing: "0.06em" }}>Contact</h4>
            <a href="mailto:inquiries@ashfordbriggs.com" style={{ display: "block", color: "var(--text-muted)", fontSize: 14, marginBottom: 8 }}>inquiries@ashfordbriggs.com</a>
            <a href="https://linkedin.com/company/ashford-briggs-llc" style={{ display: "block", color: "var(--text-muted)", fontSize: 14 }}>LinkedIn</a>
          </TextScrim>
        </div>
        <div className="container" style={{ marginTop: 40, paddingTop: 24, borderTop: "1px solid var(--border)" }}>
          <TextScrim style={{ display: "block", width: "fit-content" }} bleed={30}>
            <span style={{ color: "var(--text-dim)", fontSize: 13 }}>© 2026 Ashford & Briggs LLC. All rights reserved.</span>
          </TextScrim>
        </div>
      </footer>
    </>
  );
}
