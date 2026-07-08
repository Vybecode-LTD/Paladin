import type { CSSProperties } from "react";

interface ProductScreenshotProps {
  src: string;
  alt: string;
  /** Set true for above-the-fold usage (e.g. the hero) so it loads eagerly instead of lazily. */
  priority?: boolean;
  style?: CSSProperties;
}

/** Framed product screenshot — glass border + glow, consistent across marketing pages.
 * Fixed aspect-ratio reserves layout space so the frame doesn't collapse before the
 * image decodes (all source screenshots share a ~1917:870 dashboard aspect ratio). */
export default function ProductScreenshot({ src, alt, priority, style }: ProductScreenshotProps) {
  return (
    <div style={{ position: "relative", ...style }}>
      <div style={{
        position: "absolute", inset: -24,
        background: "radial-gradient(ellipse at center, var(--accent-glow), transparent 70%)",
        filter: "blur(32px)", opacity: 0.7, pointerEvents: "none", zIndex: -1,
      }} />
      <img
        src={src}
        alt={alt}
        loading={priority ? "eager" : "lazy"}
        // eslint-disable-next-line react/no-unknown-property -- lowercase DOM attribute; this React version doesn't map the camelCase JSX prop
        fetchpriority={priority ? "high" : "auto"}
        style={{
          display: "block",
          width: "100%",
          height: "auto",
          aspectRatio: "1917 / 870",
          objectFit: "cover",
          borderRadius: "var(--radius-lg)",
          border: "1px solid var(--border-bright)",
          boxShadow: "var(--shadow-depth-3)",
        }}
      />
    </div>
  );
}
