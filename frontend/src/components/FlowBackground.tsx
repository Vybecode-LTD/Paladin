import { useEffect, useRef } from "react";

interface Rope {
  baseY: number;
  amp1: number;
  amp2: number;
  freq1: number;
  freq2: number;
  phase: number;
  speed: number;
  depth: number; // 0 = nearest/brightest, 1 = farthest/dimmest
  hue: number;
  hueTarget: number;
  hueRate: number; // degrees/second — how fast this rope's color morphs
  vibrancy: number; // 0..1 — how saturated/present this rope is right now
  vibrancyTarget: number;
  vibrancyRate: number; // units/second — how fast vibrancy morphs
  lightA: number;
  lightB: number;
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
// deliberate swing from muted to vivid, not a barely-there nudge.
const VIBRANCY_LEVELS = [0.12, 0.4, 0.7, 1];

function pickNextVibrancy(exclude: number): number {
  const options = VIBRANCY_LEVELS.filter((v) => v !== exclude);
  return options[Math.floor(Math.random() * options.length)];
}

function buildRopes(height: number): Rope[] {
  const count = 5;
  return Array.from({ length: count }, (_, i) => {
    const depth = i / (count - 1);
    const startHue = HUES[i % HUES.length];
    const startVibrancy = VIBRANCY_LEVELS[i % VIBRANCY_LEVELS.length];
    return {
      baseY: height * (0.12 + (i / count) * 0.72 + rand(-0.04, 0.04)),
      amp1: rand(50, 90) * (1 - depth * 0.4),
      amp2: rand(20, 40) * (1 - depth * 0.4),
      freq1: rand(0.8, 1.4),
      freq2: rand(1.6, 2.6),
      phase: rand(0, Math.PI * 2),
      speed: rand(0.06, 0.12) * (1 - depth * 0.5),
      depth,
      hue: startHue,
      hueTarget: pickNextHue(startHue),
      hueRate: rand(2.5, 5), // slow — a full red->blue morph takes minutes
      vibrancy: startVibrancy,
      vibrancyTarget: pickNextVibrancy(startVibrancy),
      vibrancyRate: rand(0.015, 0.04), // a full muted<->vivid swing takes ~25-60s
      lightA: rand(38, 45),
      lightB: rand(52, 60),
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
        rope.vibrancyTarget = pickNextVibrancy(rope.vibrancyTarget);
        return;
      }
      const step = rope.vibrancyRate * dt;
      rope.vibrancy += Math.sign(delta) * Math.min(Math.abs(delta), step);
    };

    const drawRope = (rope: Rope, t: number) => {
      const step = 48;
      const points: [number, number][] = [];
      for (let x = -step; x <= width + step; x += step) {
        const y =
          rope.baseY +
          rope.amp1 * Math.sin(x * 0.0022 * rope.freq1 + rope.phase + t * rope.speed) +
          rope.amp2 * Math.sin(x * 0.004 * rope.freq2 + rope.phase * 1.6 + t * rope.speed * 0.6);
        points.push([x, y]);
      }

      // Vibrancy drives saturation/alpha/glow/width together — a rope at high
      // vibrancy reads as "more present" than its neighbors; depth still dims
      // farther ropes on top of that.
      const sat = 35 + rope.vibrancy * 43; // 35%–78%
      const alpha = (0.05 + rope.vibrancy * 0.23) * (1 - rope.depth * 0.35);
      const glow = (2 + rope.vibrancy * 7) * (1 - rope.depth * 0.4);
      const lineWidth = (0.8 + rope.vibrancy * 1.4) * (1 - rope.depth * 0.3);

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
