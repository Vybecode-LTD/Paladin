import Waveform from "@/components/Waveform";

const intel = [
  {
    border: "color-mix(in srgb, var(--glyph-violet) 35%, transparent)",
    bg: "var(--glyph-violet-bg)",
    color: "var(--glyph-violet)",
    icon: "💡",
    text: "Ask which services were migrated first — tests ownership vs. observation.",
  },
  {
    border: "color-mix(in srgb, var(--glyph-amber) 35%, transparent)",
    bg: "var(--glyph-amber-bg)",
    color: "var(--glyph-amber)",
    icon: "⚠️",
    text: <>Resume says "contributed to," not "architected."</>,
  },
  {
    border: "color-mix(in srgb, var(--glyph-cyan) 35%, transparent)",
    bg: "var(--glyph-cyan-bg)",
    color: "var(--glyph-cyan)",
    icon: "✅",
    text: "Settlement ownership confirmed — strong signal on the core requirement.",
  },
];

const scores = [
  { label: "Consistency", value: 80, color: "var(--glyph-blue)" },
  { label: "Specificity", value: 72, color: "var(--glyph-cyan)" },
  { label: "Communication", value: 70, color: "var(--glyph-amber)" },
];

/** Recreation of the Paladin live-call Intelligence Pane. Light glass —
 * matching the site's own .card material (frosted white, soft shadow)
 * rather than the dark "console" register used elsewhere, so this mockup
 * reads as an extension of the page instead of a separate dark screen. */
export default function LiveCallDemo() {
  return (
    <div style={{ position: "relative" }}>
      <div style={{
        position: "absolute", inset: -1, borderRadius: "calc(var(--radius-lg) + 1px)",
        padding: 1, background: "linear-gradient(120deg, var(--glyph-coral), var(--accent), var(--glyph-cyan))",
        opacity: 0.5, pointerEvents: "none",
      }} />

      <div style={{
        position: "relative",
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
        background: "var(--glass-bg)",
        backdropFilter: "var(--glass-blur)",
        WebkitBackdropFilter: "var(--glass-blur)",
        border: "1px solid var(--glass-border)",
        boxShadow: "var(--shadow-depth-1), inset 0 1px 0 var(--glass-highlight)",
      }}>
        <div className="signal-trace" style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, borderRadius: 0 }} />

        {/* Title bar */}
        <div style={{
          display: "flex", alignItems: "center", gap: 10,
          padding: "14px 22px", borderBottom: "1px solid var(--border)",
        }}>
          <div style={{ display: "flex", gap: 6 }}>
            {[0, 1, 2].map((i) => (
              <span key={i} style={{ width: 8, height: 8, borderRadius: 99, background: "var(--border-bright)" }} />
            ))}
          </div>
          <span className="live-dot" style={{ width: 7, height: 7, borderRadius: 99, background: "var(--glyph-cyan)", color: "var(--glyph-cyan)", marginLeft: 6 }} />
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--text)" }}>
            Paladin — call in progress · 07:42
          </span>
        </div>

        {/* Transcript + Intelligence */}
        <div className="live-call-grid">
          <div style={{ padding: "24px 26px", borderRight: "1px solid var(--border)" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, letterSpacing: "0.08em", color: "var(--text-dim)", marginBottom: 18 }}>
              LIVE TRANSCRIPT
            </div>
            <p style={{ fontSize: 15, color: "var(--text)", marginBottom: 16, lineHeight: 1.55 }}>
              <strong style={{ color: "var(--glyph-violet)" }}>Candidate:</strong> "...I architected the entire payment platform migration..."
            </p>
            <p style={{ fontSize: 15, color: "var(--text)", marginBottom: 16, lineHeight: 1.55 }}>
              <strong style={{ color: "var(--glyph-cyan)" }}>You:</strong> "Which team owned settlement during the cutover?"
            </p>
            <p style={{ fontSize: 15, color: "var(--text)", marginBottom: 24, lineHeight: 1.55 }}>
              <strong style={{ color: "var(--glyph-violet)" }}>Candidate:</strong> "Mine — I signed off on every settlement run myself."
            </p>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <Waveform onLight />
              <span style={{ fontSize: 13, color: "var(--text-dim)" }}>transcribing live...</span>
            </div>
          </div>

          <div style={{ padding: "24px 26px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, letterSpacing: "0.08em", color: "var(--text-dim)", marginBottom: 18 }}>
              INTELLIGENCE
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 14, marginBottom: 22 }}>
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
            <div style={{ borderTop: "1px solid var(--border)", paddingTop: 18 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {scores.map((s) => (
                  <div key={s.label}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5, fontSize: 12, color: "var(--text-dim)" }}>
                      <span>{s.label}</span>
                      <span style={{ color: "var(--text)", fontFamily: "var(--font-mono)" }}>{s.value}%</span>
                    </div>
                    <div style={{ height: 4, borderRadius: 99, background: "var(--border)", overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${s.value}%`, borderRadius: 99, background: s.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
