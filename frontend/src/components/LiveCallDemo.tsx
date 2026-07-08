const BARS = [
  { h: 9, delay: 0.0, dur: 1.0 },
  { h: 15, delay: 0.08, dur: 0.85 },
  { h: 21, delay: 0.16, dur: 1.05 },
  { h: 13, delay: 0.24, dur: 0.9 },
  { h: 23, delay: 0.05, dur: 1.15 },
  { h: 11, delay: 0.32, dur: 0.95 },
  { h: 19, delay: 0.12, dur: 1.0 },
  { h: 24, delay: 0.28, dur: 0.8 },
  { h: 14, delay: 0.02, dur: 1.1 },
  { h: 10, delay: 0.36, dur: 0.9 },
  { h: 18, delay: 0.18, dur: 1.05 },
  { h: 12, delay: 0.22, dur: 0.85 },
  { h: 20, delay: 0.1, dur: 1.0 },
  { h: 8, delay: 0.3, dur: 0.95 },
];

function Waveform() {
  return (
    <div className="waveform" aria-hidden="true">
      {BARS.map((b, i) => (
        <span
          key={i}
          style={{
            height: b.h,
            animationDelay: `${b.delay}s`,
            animationDuration: `${b.dur}s`,
          }}
        />
      ))}
    </div>
  );
}

const intel = [
  {
    tone: "violet",
    icon: "💡",
    border: "rgba(139, 124, 240, 0.4)",
    bg: "rgba(139, 124, 240, 0.1)",
    color: "#c4bdf7",
    text: "Ask which services were migrated first — tests ownership vs. observation.",
  },
  {
    tone: "amber",
    icon: "⚠️",
    border: "rgba(232, 179, 79, 0.4)",
    bg: "rgba(232, 179, 79, 0.1)",
    color: "#f2c879",
    text: <>Resume says "contributed to," not "architected."</>,
  },
];

/** Recreation of the Paladin live-call Intelligence Pane — dark glass console
 * with an animated transcribing waveform, shown as a marketing centerpiece. */
export default function LiveCallDemo() {
  return (
    <div style={{ position: "relative" }}>
      <div style={{
        position: "absolute", top: "-15%", left: "2%", width: 280, height: 280,
        background: "radial-gradient(circle, rgba(255,140,105,0.35), transparent 70%)",
        filter: "blur(50px)", pointerEvents: "none",
      }} />
      <div style={{
        position: "absolute", bottom: "-20%", left: "28%", width: 340, height: 340,
        background: "radial-gradient(circle, rgba(200,100,220,0.28), transparent 70%)",
        filter: "blur(55px)", pointerEvents: "none",
      }} />
      <div style={{
        position: "absolute", top: "-12%", right: "3%", width: 260, height: 260,
        background: "radial-gradient(circle, rgba(255,180,90,0.3), transparent 70%)",
        filter: "blur(50px)", pointerEvents: "none",
      }} />

      <div style={{
        position: "relative",
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
        background: "rgba(13, 15, 20, 0.88)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        boxShadow: "var(--shadow-depth-3)",
      }}>
        {/* Title bar */}
        <div style={{
          display: "flex", alignItems: "center", gap: 10,
          padding: "14px 22px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        }}>
          <div style={{ display: "flex", gap: 6 }}>
            {[0, 1, 2].map((i) => (
              <span key={i} style={{ width: 8, height: 8, borderRadius: 99, background: "rgba(255,255,255,0.22)" }} />
            ))}
          </div>
          <span className="live-dot" style={{ width: 7, height: 7, borderRadius: 99, background: "#22d3ee", color: "#22d3ee", marginLeft: 6 }} />
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "rgba(255,255,255,0.75)" }}>
            Paladin — call in progress · 07:42
          </span>
        </div>

        {/* Transcript + Intelligence */}
        <div className="live-call-grid">
          <div style={{ padding: "24px 26px", borderRight: "1px solid rgba(255,255,255,0.08)" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, letterSpacing: "0.08em", color: "rgba(255,255,255,0.4)", marginBottom: 18 }}>
              LIVE TRANSCRIPT
            </div>
            <p style={{ fontSize: 15, color: "rgba(255,255,255,0.85)", marginBottom: 16, lineHeight: 1.55 }}>
              <strong style={{ color: "#a5a8f5" }}>Candidate:</strong> "...I architected the entire payment platform migration..."
            </p>
            <p style={{ fontSize: 15, color: "rgba(255,255,255,0.85)", marginBottom: 24, lineHeight: 1.55 }}>
              <strong style={{ color: "#5fd4e0" }}>You:</strong> "Which team owned settlement during the cutover?"
            </p>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <Waveform />
              <span style={{ fontSize: 13, color: "rgba(255,255,255,0.4)" }}>transcribing live...</span>
            </div>
          </div>

          <div style={{ padding: "24px 26px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, letterSpacing: "0.08em", color: "rgba(255,255,255,0.4)", marginBottom: 18 }}>
              INTELLIGENCE
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {intel.map((c, i) => (
                <div key={i} style={{
                  padding: "13px 15px", borderRadius: 10,
                  border: `1px solid ${c.border}`, background: c.bg, color: c.color,
                  fontSize: 14, lineHeight: 1.55,
                }}>
                  {c.icon} {c.text}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
