import { NavLink, Outlet } from "react-router-dom";

/** Shell for the Analytics tab.
 *
 * One sidebar entry with its own tab bar, rather than five more entries in a
 * sidebar that already has five. The views here belong together — a campaign,
 * its numbers and the people it went to are one subject — and separating them
 * in the main navigation would bury that.
 */

const TABS = [
  { to: "/admin/analytics", label: "Overview", end: true },
  { to: "/admin/analytics/campaigns", label: "Campaigns", end: false },
  { to: "/admin/analytics/contacts", label: "Contacts", end: false },
  { to: "/admin/analytics/trust", label: "Domain trust", end: false },
];

export default function AnalyticsLayout() {
  return (
    <div>
      <h1 style={{ fontSize: 30, fontWeight: 800, marginBottom: 6 }}>Analytics</h1>
      <p style={{ fontSize: 14, color: "var(--text-muted)", maxWidth: "72ch", lineHeight: 1.55, marginBottom: 20 }}>
        Campaign results, with every figure labelled by how much it can be trusted.
        Roughly half of all email opens industry-wide are automatic prefetch rather
        than people, so opens and clicks are shown split between what is probably a
        machine and what might be a person.
      </p>

      <nav
        style={{
          display: "flex", gap: 4, borderBottom: "1px solid var(--border)",
          marginBottom: 24, flexWrap: "wrap",
        }}
      >
        {TABS.map(({ to, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            style={({ isActive }) => ({
              padding: "9px 14px",
              fontSize: 14,
              fontWeight: 600,
              color: isActive ? "var(--accent)" : "var(--text-muted)",
              // Sits on top of the container's border so the active tab reads
              // as connected to the panel below it.
              borderBottom: `2px solid ${isActive ? "var(--accent)" : "transparent"}`,
              marginBottom: -1,
              textDecoration: "none",
            })}
          >
            {label}
          </NavLink>
        ))}
      </nav>

      <Outlet />
    </div>
  );
}
