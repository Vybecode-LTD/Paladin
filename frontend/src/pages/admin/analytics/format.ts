/** Formatting helpers for the Analytics screens.
 *
 * Kept out of parts.tsx because a file that exports both components and plain
 * functions breaks React Fast Refresh, which the project's lint config flags.
 */

/** The classifier stores machine-readable reasons; people read this screen. */
export function readableReason(reason: string): string {
  const known: Record<string, string> = {
    "google-image-proxy": "Gmail image proxy",
    "yahoo-mail-proxy": "Yahoo mail proxy",
    "apple-mpp": "Apple privacy prefetch",
    "prefetch-timing": "opened within seconds of sending",
    "scanner-sweep": "security scan (walked every link)",
    "click-unconfirmed": "not confirmed by the landing page",
    unclassified: "no machine signature",
    "no-user-agent": "no browser identified",
    "beacon-confirmed": "confirmed by the landing page",
    "unsubscribe-link": "unsubscribe link",
  };
  if (known[reason]) return known[reason];
  if (reason.startsWith("scanner-referer:")) return `security scan via ${reason.split(":")[1]}`;
  if (reason.startsWith("scanner:")) return `security scan (${reason.slice(8)})`;
  if (reason.startsWith("product:")) return reason.slice(8).replace(/_/g, " ");
  return reason;
}

/** A percentage, or an em dash when there is nothing to divide by — never
 * "0.0%", which reads as a measured zero rather than an absence of data. */
export function pct(numerator: number, denominator: number): string {
  if (!denominator) return "—";
  return `${((numerator / denominator) * 100).toFixed(1)}%`;
}
