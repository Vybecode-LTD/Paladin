import { useEffect, useRef } from "react";

interface Rope {
  baseY: number;
  amp1: number;
  amp2: number;
  amp3: number;
  freq1: number;
  freq2: number;
  freq3: number;
  // Each harmonic gets its own fully independent phase (not derived from one
  // shared value) — that shared-derivation was why every rope's two humps
  // moved in the same fixed relationship, making them all read as the same
  // underlying shape shifted around, rather than genuinely independent.
  phase1: number;
  phase2: number;
  phase3: number;
  // A large per-rope shift in x-space so two ropes with similar wavelengths
  // still never crest at the same x at the same time.
  xOffset: number;
  // Asymmetric warp: crests and troughs scale differently, so the silhouette
  // is not a mirror-symmetric sine — each rope leans its own direction.
  skew: number;
  speed: number;
  depth: number; // 0 = nearest/brightest, 1 = farthest/dimmest
  hue: number;
  hueTarget: number;
  hueRate: number; // degrees/second — how fast this rope's color morphs
  vibrancy: number; // 0..1 (up to ~1.6 for the pulse hero) — how saturated/present this rope is right now
  vibrancyTarget: number;
  vibrancyRate: number; // units/second — how fast vibrancy morphs
  vibrancyLevels: number[]; // this rope's own set of levels to swing between
  lightA: number;
  lightB: number;
  isPulseHero: boolean; // the one rope that pulses noticeably harder than its neighbors
}

function rand(min: number, max: number): number {
  return min + Math.random() * (max - min);
}

// Target hues each rope slowly morphs between — red, yellow, green, blue.
// Interpolating through hue angle (not RGB) keeps the in-between colors
// vivid instead of passing through muddy browns/greys.
const HUES = [8, 50, 145, 228];

function pickNextHue(exclude: number): number {
  const options = HUES.filter((h) => h !== exclude);
  return options[Math.floor(Math.random() * options.length)];
}

function hueDelta(from: number, to: number): number {
  let d = (to - from) % 360;
  if (d > 180) d -= 360;
  if (d < -180) d += 360;
  return d;
}

// Discrete levels (not a free-floating random) so each transition reads as a
// deliberate swing from muted to vivid, not a barely-there nudge. The pulse
// hero gets its own wider, more dramatic set (overshoots past 1 for a
// genuinely heavier peak) so exactly one rope reads as "pulsing hard"
// against calmer neighbors.
const VIBRANCY_LEVELS = [0.18, 0.4, 0.6, 0.85];
const HERO_VIBRANCY_LEVELS = [0.2, 0.7, 1.15, 1.6];

function pickNextVibrancy(exclude: number, levels: number[]): number {
  const options = levels.filter((v) => v !== exclude);
  return options[Math.floor(Math.random() * options.length)];
}

function buildRopes(height: number): Rope[] {
  const count = 5;
  const heroIndex = Math.floor(Math.random() * count);
  return Array.from({ length: count }, (_, i) => {
    const depth = i / (count - 1);
    const isPulseHero = i === heroIndex;
    const levels = isPulseHero ? HERO_VIBRANCY_LEVELS : VIBRANCY_LEVELS;
    const startHue = HUES[i % HUES.length];
    const startVibrancy = levels[i % levels.length];
    return {
      // Depth still separates "near" from "far," but gently — every rope
      // should read as clearly moving, not just the front couple.
      // Wider, non-overlapping-feeling jitter on vertical placement too, so
      // the 5 baselines don't read as an evenly-ruled grid.
      baseY: height * (0.1 + (i / count) * 0.72 + rand(-0.09, 0.09)),
      amp1: rand(45, 95) * (1 - depth * 0.15),
      amp2: rand(18, 42) * (1 - depth * 0.15),
      amp3: rand(7, 20) * (1 - depth * 0.15),
      freq1: rand(0.55, 1.65),
      freq2: rand(1.7, 3.1),
      freq3: rand(3.4, 5.8),
      phase1: rand(0, Math.PI * 2),
      phase2: rand(0, Math.PI * 2),
      phase3: rand(0, Math.PI * 2),
      xOffset: rand(0, 50000),
      skew: rand(-0.4, 0.4),
      speed: rand(0.09, 0.16) * (1 - depth * 0.2),
      depth,
      hue: startHue,
      hueTarget: pickNextHue(startHue),
      hueRate: rand(4, 7), // a full red->blue morph takes roughly a minute or two
      vibrancy: startVibrancy,
      vibrancyTarget: pickNextVibrancy(startVibrancy, levels),
      // Hero pulses noticeably faster (a full swing in ~10-18s) than the
      // calmer neighbors (~30-55s).
      vibrancyRate: isPulseHero ? rand(0.09, 0.15) : rand(0.018, 0.033),
      vibrancyLevels: levels,
      lightA: rand(38, 45),
      lightB: rand(52, 60),
      isPulseHero,
    };
  });
}

// Ambient, minimal, always-on background: a few slow flowing gradient
// "ropes" of light at varying simulated depth, behind a static CSS vignette.
export default function FlowBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvasEl = canvasRef.current;
    if (!canvasEl) return;
    const context = canvasEl.getContext("2d");
    if (!context) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    let width = 0;
    let height = 0;
    let ropes: Rope[] = [];

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvasEl.width = width * dpr;
      canvasEl.height = height * dpr;
      canvasEl.style.width = `${width}px`;
      canvasEl.style.height = `${height}px`;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      ropes = buildRopes(height);
    };
    resize();
    window.addEventListener("resize", resize);

    const updateHue = (rope: Rope, dt: number) => {
      const delta = hueDelta(rope.hue, rope.hueTarget);
      if (Math.abs(delta) < 0.5) {
        rope.hueTarget = pickNextHue(rope.hueTarget);
        return;
      }
      const step = rope.hueRate * dt;
      rope.hue = (rope.hue + Math.sign(delta) * Math.min(Math.abs(delta), step) + 360) % 360;
    };

    const updateVibrancy = (rope: Rope, dt: number) => {
      const delta = rope.vibrancyTarget - rope.vibrancy;
      if (Math.abs(delta) < 0.01) {
        rope.vibrancyTarget = pickNextVibrancy(rope.vibrancyTarget, rope.vibrancyLevels);
        return;
      }
      const step = rope.vibrancyRate * dt;
      rope.vibrancy += Math.sign(delta) * Math.min(Math.abs(delta), step);
    };

    const drawRope = (rope: Rope, t: number) => {
      const step = 48;
      const points: [number, number][] = [];
      for (let x = -step; x <= width + step; x += step) {
        const xs = x + rope.xOffset;
        const raw =
          rope.amp1 * Math.sin(xs * 0.0022 * rope.freq1 + rope.phase1 + t * rope.speed) +
          rope.amp2 * Math.sin(xs * 0.004 * rope.freq2 + rope.phase2 + t * rope.speed * 0.6) +
          rope.amp3 * Math.sin(xs * 0.0065 * rope.freq3 + rope.phase3 + t * rope.speed * 1.35);
        // Scale crests and troughs unevenly — kills the mirror symmetry a
        // pure sine sum still has around its own baseline.
        const warped = raw >= 0 ? raw * (1 + rope.skew) : raw * (1 - rope.skew);
        points.push([x, rope.baseY + warped]);
      }

      // Vibrancy drives saturation/alpha/glow/width together — a rope at high
      // vibrancy reads as "more present" than its neighbors. Depth still adds
      // a little separation, but gently now — every rope should read as
      // clearly, visibly moving, not just the front couple. The pulse hero
      // gets an extra multiplier on top so its swings read as heavier, not
      // just wider.
      const heroBoost = rope.isPulseHero ? 1.3 : 1;
      const sat = Math.min(100, 40 + rope.vibrancy * 40);
      const alpha = Math.min(0.6, (0.08 + rope.vibrancy * 0.22) * (1 - rope.depth * 0.18) * heroBoost);
      const glow = (3 + rope.vibrancy * 8) * (1 - rope.depth * 0.2) * heroBoost;
      const lineWidth = (1 + rope.vibrancy * 1.4) * (1 - rope.depth * 0.15) * (rope.isPulseHero ? 1.15 : 1);

      const colA = `hsl(${rope.hue}, ${sat}%, ${rope.lightA}%)`;
      const colB = `hsl(${rope.hue}, ${sat}%, ${rope.lightB}%)`;
      const colAFade = `hsla(${rope.hue}, ${sat}%, ${rope.lightA}%, 0)`;
      const grad = context.createLinearGradient(0, 0, width, 0);
      grad.addColorStop(0, colAFade);
      grad.addColorStop(0.15, colA);
      grad.addColorStop(0.5, colB);
      grad.addColorStop(0.85, colA);
      grad.addColorStop(1, colAFade);

      context.beginPath();
      context.moveTo(points[0][0], points[0][1]);
      for (let i = 1; i < points.length - 1; i++) {
        const [cx, cy] = points[i];
        const [nx, ny] = points[i + 1];
        context.quadraticCurveTo(cx, cy, (cx + nx) / 2, (cy + ny) / 2);
      }
      context.strokeStyle = grad;
      context.lineWidth = lineWidth;
      context.globalAlpha = alpha;
      context.shadowColor = colB;
      context.shadowBlur = glow;
      context.stroke();
    };

    const render = (t: number, dt: number) => {
      context.clearRect(0, 0, width, height);
      // "source-over": on a light background, additive blending washes color
      // toward white instead of deepening it — normal blending keeps these
      // reading as precise saturated ink lines rather than a glow.
      for (const rope of ropes) {
        updateHue(rope, dt);
        updateVibrancy(rope, dt);
        drawRope(rope, t);
      }
      context.globalAlpha = 1;
    };

    render(0, 0); // paint the first frame immediately, don't wait on the first rAF tick

    if (reduceMotion) {
      return () => window.removeEventListener("resize", resize);
    }

    let raf = 0;
    let t = 0;
    let last = performance.now();
    let running = true;
    function onVisibility() {
      running = document.visibilityState === "visible";
      last = performance.now();
    }
    document.addEventListener("visibilitychange", onVisibility);

    function frame(now: number) {
      raf = requestAnimationFrame(frame);
      if (!running) return;
      const dt = Math.min((now - last) / 1000, 0.05);
      t += dt;
      last = now;
      render(t, dt);
    }
    raf = requestAnimationFrame(frame);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, []);

  return (
    <div
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: -1,
        background:
          "radial-gradient(ellipse 80% 55% at 50% -10%, rgba(0,118,209,0.05), transparent 60%), " +
          "radial-gradient(ellipse 60% 50% at 100% 100%, rgba(96,68,205,0.045), transparent 60%), " +
          "var(--bg)",
      }}
    >
      <canvas ref={canvasRef} style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }} />
    </div>
  );
}
