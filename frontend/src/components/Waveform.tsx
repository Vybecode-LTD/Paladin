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

interface WaveformProps {
  /** "thin" for inline/dense usage (admin busy states, form success). */
  size?: "default" | "thin";
  /** Bars hold still at low opacity — used for the "static competitor" side
   * of a live-vs-static comparison. */
  frozen?: boolean;
  /** Use the accent blue instead of the console's light-on-dark blue — for
   * placement directly on the site's light background rather than inside
   * the dark LiveCallDemo console. */
  onLight?: boolean;
  /** How many of the 14 bars to render — trims from the ends symmetrically. */
  bars?: number;
}

/** The site's signature "live signal" motif — reused anywhere the product's
 * real-time nature should read visually instead of a generic spinner/icon. */
export default function Waveform({ size = "default", frozen = false, onLight = false, bars = 14 }: WaveformProps) {
  const start = Math.floor((BARS.length - bars) / 2);
  const shown = BARS.slice(start, start + bars);
  const classes = [
    "waveform",
    size === "thin" && "waveform-thin",
    frozen && "waveform-frozen",
    onLight && "waveform-onlight",
  ].filter(Boolean).join(" ");

  return (
    <div className={classes} aria-hidden="true">
      {shown.map((b, i) => (
        <span
          key={i}
          style={{
            height: b.h,
            animationDelay: frozen ? undefined : `${b.delay}s`,
            animationDuration: frozen ? undefined : `${b.dur}s`,
          }}
        />
      ))}
    </div>
  );
}
