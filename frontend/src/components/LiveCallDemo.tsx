import Waveform from "@/components/Waveform";

const intel = [
  {
    border: "color-mix(in srgb, var(--console-glyph-violet) 40%, transparent)",
    bg: "color-mix(in srgb, var(--console-glyph-violet) 10%, transparent)",
    color: "var(--console-glyph-violet)",
    icon: "💡",
    text: "Ask which services were migrated first — tests ownership vs. observation.",
  },
  {
    border: "color-mix(in srgb, var(--console-glyph-amber) 40%, transparent)",
    bg: "color-mix(in srgb, var(--console-glyph-amber) 10%, transparent)",
    color: "var(--console-glyph-amber)",
    icon: "⚠️",
    text: <>Resume says "contributed to," not "architected."</>,
  },
  {
    border: "color-mix(in srgb, var(--console-glyph-cyan) 40%, transparent)",
    bg: "color-mix(in srgb, var(--console-glyph-cyan) 10%, transparent)",
    color: "var(--console-glyph-cyan)",
    icon: "✅",
    text: "Settlement ownership confirmed — strong signal on the core requirement.",
  },
];

const scores = [
  { label: "Consistency", value: 80, color: "var(--console-glyph-blue)" },
  { label: "Specificity", value: 72, color: "var(--console-glyph-cyan)" },
  { label: "Communication", value: 70, color: "var(--console-glyph-amber)" },
];

/** Recreation of the Paladin live-call Intelligence Pane — the "console"
 * register: the site's one deliberate second material (dark glass, a screen
 * within the page), palette pulled from --console-* tokens rather than
 * one-off hex, structural signal-trace instead of decorative gradient blobs. */
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
        background: "var(--console-bg)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        boxShadow: "var(--shadow-depth-3)",
      }}>
        <div className="signal-trace" style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, borderRadius: 0 }} />

        {/* Title bar */}
        <div style={{
          display: "flex", alignItems: "center", gap: 10,
          padding: "14px 22px", borderBottom: "1px solid var(--console-border)",
        }}>
          <div style={{ display: "flex", gap: 6 }}>
            {[0, 1, 2].map((i) => (
              <span key={i} style={{ width: 8, height: 8, borderRadius: 99, background: "rgba(255,255,255,0.22)" }} />
            ))}
          </div>
          <span className="live-dot" style={{ width: 7, height: 7, borderRadius: 99, background: "var(--console-glyph-cyan)", color: "var(--console-glyph-cyan)", marginLeft: 6 }} />
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--console-text)" }}>
            Paladin — call in progress · 07:42
          </span>
        </div>

        {/* Transcript + Intelligence */}
        <div className="live-call-grid">
          <div style={{ padding: "24px 26px", borderRight: "1px solid var(--console-border)" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, letterSpacing: "0.08em", color: "var(--console-text-dim)", marginBottom: 18 }}>
              LIVE TRANSCRIPT
            </div>
            <p style={{ fontSize: 15, color: "var(--console-text)", marginBottom: 16, lineHeight: 1.55 }}>
              <strong style={{ color: "var(--console-glyph-violet)" }}>Candidate:</strong> "...I architected the entire payment platform migration..."
            </p>
            <p style={{ fontSize: 15, color: "var(--console-text)", marginBottom: 16, lineHeight: 1.55 }}>
              <strong style={{ color: "var(--console-glyph-cyan)" }}>You:</strong> "Which team owned settlement during the cutover?"
            </p>
            <p style={{ fontSize: 15, color: "var(--console-text)", marginBottom: 24, lineHeight: 1.55 }}>
              <strong style={{ color: "var(--console-glyph-violet)" }}>Candidate:</strong> "Mine — I signed off on every settlement run myself."
            </p>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <Waveform />
              <span style={{ fontSize: 13, color: "var(--console-text-dim)" }}>transcribing live...</span>
            </div>
          </div>

          <div style={{ padding: "24px 26px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, letterSpacing: "0.08em", color: "var(--console-text-dim)", marginBottom: 18 }}>
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
            <div style={{ borderTop: "1px solid var(--console-border)", paddingTop: 18 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {scores.map((s) => (
                  <div key={s.label}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5, fontSize: 12, color: "var(--console-text-dim)" }}>
                      <span>{s.label}</span>
                      <span style={{ color: "var(--console-text)", fontFamily: "var(--font-mono)" }}>{s.value}%</span>
                    </div>
                    <div style={{ height: 4, borderRadius: 99, background: "var(--console-border)", overflow: "hidden" }}>
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
