import { useReducedMotion } from "framer-motion";

/** Standard scroll-triggered reveal for headings/body copy/sections — the
 * one motion idea used site-wide, now actually honoring the OS
 * prefers-reduced-motion setting (previously only FlowBackground did). */
export function useFadeUp() {
  const reduceMotion = useReducedMotion();
  return {
    initial: reduceMotion ? { opacity: 1 } : { opacity: 0, y: 24 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true, margin: "-80px" },
    transition: { duration: reduceMotion ? 0 : 0.5 },
  };
}

/** Card-grid variant — glass "focusing into view" (scale + blur-in) instead
 * of sliding up, a small coherent extension of the precision-glass material
 * rather than an unrelated motion idea. */
export function useGlassReveal() {
  const reduceMotion = useReducedMotion();
  return {
    initial: reduceMotion ? { opacity: 1 } : { opacity: 0, scale: 0.97, filter: "blur(6px)" },
    whileInView: { opacity: 1, scale: 1, filter: "blur(0px)" },
    viewport: { once: true, margin: "-80px" },
    transition: { duration: reduceMotion ? 0 : 0.5 },
  };
}
