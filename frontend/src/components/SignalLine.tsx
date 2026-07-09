import { useRef, type ReactNode } from "react";
import { motion, useScroll, useTransform, useReducedMotion } from "framer-motion";

interface SignalLineProps {
  children: ReactNode;
}

/** A vertical signal spine that draws itself in as the user scrolls past it —
 * the timeline-spine variant of the site's signal-line motif (see also the
 * CSS-only .signal-trace sweep used for flat dividers). Wrap a column of
 * waypoint rows; each row should be `position: relative` with left padding
 * to clear the spine. */
export default function SignalLine({ children }: SignalLineProps) {
  const ref = useRef<HTMLDivElement>(null);
  const reduceMotion = useReducedMotion();
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start 0.75", "end 0.6"],
  });
  const pathLength = useTransform(scrollYProgress, [0, 1], [0, 1]);

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <div style={{ position: "absolute", left: 27, top: 8, bottom: 8, width: 2, zIndex: 0 }} aria-hidden="true">
        <svg width="2" height="100%" style={{ position: "absolute", inset: 0, overflow: "visible" }} preserveAspectRatio="none">
          <line x1="1" y1="0" x2="1" y2="100%" stroke="var(--border)" strokeWidth="2" />
          <motion.line
            x1="1" y1="0" x2="1" y2="100%"
            stroke="var(--accent)" strokeWidth="2"
            style={reduceMotion ? undefined : { pathLength }}
            pathLength={reduceMotion ? 1 : undefined}
          />
        </svg>
      </div>
      <div style={{ position: "relative", zIndex: 1, display: "flex", flexDirection: "column", gap: 20 }}>
        {children}
      </div>
    </div>
  );
}
