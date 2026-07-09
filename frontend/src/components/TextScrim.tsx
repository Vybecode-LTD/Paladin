import type { ReactNode, CSSProperties } from "react";

interface TextScrimProps {
  children: ReactNode;
  style?: CSSProperties;
  /** How far the scrim bleeds past the content on every side before it
   * finishes feathering out. Default 70px. */
  bleed?: number;
}

/** Wraps text content with a scrim that blurs and dims the FlowBackground
 * waves specifically where they pass behind it, so the waves read as
 * "further back" / out of focus instead of competing with the copy.
 * Feathers on all four edges (a plain horizontal gradient for left/right, a
 * plain vertical one for top/bottom, combined via mask-composite:intersect)
 * — no hard rectangular edge. Both gradients are pinned to a cardinal axis
 * (90deg/180deg) rather than an angled one deliberately: an angled gradient's
 * line length scales with BOTH width and height of the box, so on a very
 * tall, narrow box (a long legal document, say) the percentage-based color
 * stops stop lining up with the visible width at all — the scrim collapses
 * to a thin diagonal stripe instead of covering the text. A cardinal-axis
 * gradient's length depends on only one dimension, so it stays correct
 * regardless of the wrapped content's aspect ratio. isolation:isolate scopes
 * the scrim's negative z-index to this wrapper only, so it can't affect
 * anything outside it. */
export default function TextScrim({ children, style, bleed = 70 }: TextScrimProps) {
  return (
    <div style={{ position: "relative", isolation: "isolate", ...style }}>
      <div aria-hidden="true" style={{
        position: "absolute", inset: -bleed, zIndex: -1,
        backdropFilter: "blur(20px)", WebkitBackdropFilter: "blur(20px)",
        background: "color-mix(in srgb, var(--bg) 60%, transparent)",
        WebkitMaskImage:
          "linear-gradient(90deg, transparent 0%, black 12%, black 88%, transparent 100%), " +
          "linear-gradient(to bottom, transparent 0%, black 22%, black 78%, transparent 100%)",
        maskImage:
          "linear-gradient(90deg, transparent 0%, black 12%, black 88%, transparent 100%), " +
          "linear-gradient(to bottom, transparent 0%, black 22%, black 78%, transparent 100%)",
        WebkitMaskComposite: "source-in",
        maskComposite: "intersect",
        pointerEvents: "none",
      }} />
      {children}
    </div>
  );
}
