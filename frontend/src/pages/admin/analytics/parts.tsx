/** Shared pieces for the Analytics screens.
 *
 * The tier chip and the split bar are the two that matter. Every figure on
 * these pages carries a tier, and every inferred figure is drawn as a split
 * rather than a total — because a single "open rate" is about half automatic
 * prefetch, and a number with a percent sign next to it gets believed.
 */
import type { ReactNode } from "react";
import { readableReason } from "./format";

export type Tier = "exact" | "verified" | "inferred" | "derived";

const TIER_STYLE: Record<Tier, { color: string; bg: string; label: string; title: string }> = {
  exact: {
    color: "var(--glyph-blue)", bg: "var(--glyph-blue-bg)", label: "Exact",
    title: "The mail system told us this. It cannot be wrong.",
  },
  verified: {
    color: "var(--success)", bg: "var(--glyph-cyan-bg)", label: "Verified",
    title: "A person did something a machine cannot fake — ran the page, wrote a reply, or used the product.",
  },
  inferred: {
    color: "var(--warning)", bg: "var(--glyph-amber-bg)", label: "Inferred",
    title: "A signal machines also produce. Filtered as well as we can, but never proof of a person.",
  },
  derived: {
    color: "var(--text-muted)", bg: "var(--bg-elevated)", label: "Derived",
    title: "Computed from the figures above.",
  },
};

export function TierChip({ tier }: { tier: Tier }) {
  const s = TIER_STYLE[tier];
  return (
    <span
      title={s.title}
      style={{
        display: "inline-block", fontSize: 10, fontWeight: 700,
        letterSpacing: ".07em", textTransform: "uppercase",
        padding: "2px 7px", borderRadius: 4, whiteSpace: "nowrap",
        color: s.color, background: s.bg, verticalAlign: "middle",
      }}
    >
      {s.label}
    </span>
  );
}

export function Section({
  title, tier, note, children,
}: {
  title: string; tier: Tier; note?: string; children: ReactNode;
}) {
  return (
    <section style={{ marginBottom: 30 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
        <h2 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>{title}</h2>
        <TierChip tier={tier} />
      </div>
      {note && (
        <p style={{ fontSize: 13, color: "var(--text-muted)", margin: "0 0 12px", maxWidth: "70ch", lineHeight: 1.5 }}>
          {note}
        </p>
      )}
      {children}
    </section>
  );
}

/** A big number with a label under it. */
export function Stat({
  value, label, hint, tone,
}: {
  value: ReactNode; label: string; hint?: string; tone?: "good" | "warn" | "bad";
}) {
  const color =
    tone === "good" ? "var(--success)" :
    tone === "warn" ? "var(--warning)" :
    tone === "bad" ? "var(--danger)" : "var(--text)";
  return (
    <div>
      <div style={{ fontSize: 26, fontWeight: 700, lineHeight: 1.1, color, fontVariantNumeric: "tabular-nums" }}>
        {value}
      </div>
      <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 3 }}>{label}</div>
      {hint && (
        <div style={{ fontSize: 11, color: "var(--text-dim)", marginTop: 2, lineHeight: 1.45 }}>{hint}</div>
      )}
    </div>
  );
}

export function StatRow({ children, columns = 4 }: { children: ReactNode; columns?: number }) {
  return (
    <div
      className="card"
      style={{
        display: "grid",
        gridTemplateColumns: `repeat(auto-fit, minmax(${Math.floor(680 / columns)}px, 1fr))`,
        gap: 20,
      }}
    >
      {children}
    </div>
  );
}

/** The split bar: how much of an inferred figure is machine traffic.
 *
 * Drawn rather than stated because the proportion is the point. Seeing that
 * half the bar is amber is what stops someone quoting the total in a board
 * meeting.
 */
export function SplitBar({
  machine, human, machineLabel = "machine", humanLabel = "possibly human",
}: {
  machine: number; human: number; machineLabel?: string; humanLabel?: string;
}) {
  const total = machine + human;
  if (total === 0) {
    return <p style={{ fontSize: 13, color: "var(--text-dim)", margin: 0 }}>Nothing recorded yet.</p>;
  }
  const pct = (n: number) => (n / total) * 100;
  return (
    <div>
      <div
        style={{ display: "flex", height: 10, borderRadius: 5, overflow: "hidden", background: "var(--bg-elevated)" }}
        role="img"
        aria-label={`${machine} ${machineLabel}, ${human} ${humanLabel}`}
      >
        {machine > 0 && <div style={{ width: `${pct(machine)}%`, background: "var(--warning)" }} />}
        {human > 0 && <div style={{ width: `${pct(human)}%`, background: "var(--accent)" }} />}
      </div>
      <div style={{ display: "flex", gap: 18, marginTop: 8, fontSize: 12, flexWrap: "wrap" }}>
        <Legend color="var(--warning)" label={`${machine.toLocaleString()} ${machineLabel}`} />
        <Legend color="var(--accent)" label={`${human.toLocaleString()} ${humanLabel}`} />
      </div>
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "var(--text-muted)" }}>
      <span style={{ width: 9, height: 9, borderRadius: 2, background: color, display: "inline-block" }} />
      {label}
    </span>
  );
}

/** Names the machines that were filtered out, with counts. */
export function Breakdown({ items }: { items: Record<string, number> }) {
  const entries = Object.entries(items);
  if (entries.length === 0) return null;
  return (
    <ul style={{ listStyle: "none", padding: 0, margin: "10px 0 0", display: "flex", flexWrap: "wrap", gap: "6px 8px" }}>
      {entries.map(([reason, count]) => (
        <li
          key={reason}
          style={{
            fontSize: 11.5, color: "var(--text-muted)", background: "var(--bg-elevated)",
            padding: "3px 8px", borderRadius: 4, fontFamily: "var(--font-mono)",
          }}
        >
          {readableReason(reason)} <b style={{ color: "var(--text)" }}>{count}</b>
        </li>
      ))}
    </ul>
  );
}

export function StatusChip({ status }: { status: string }) {
  const tone: Record<string, [string, string]> = {
    draft: ["var(--text-muted)", "var(--bg-elevated)"],
    scheduled: ["var(--glyph-violet)", "var(--glyph-violet-bg)"],
    sending: ["var(--warning)", "var(--glyph-amber-bg)"],
    sent: ["var(--success)", "var(--glyph-cyan-bg)"],
    failed: ["var(--danger)", "var(--glyph-coral-bg)"],
  };
  const [color, bg] = tone[status] ?? tone.draft;
  return (
    <span style={{
      display: "inline-block", fontSize: 11, fontWeight: 600, letterSpacing: ".05em",
      textTransform: "uppercase", padding: "3px 9px", borderRadius: 5, color, background: bg,
    }}>
      {status}
    </span>
  );
}

