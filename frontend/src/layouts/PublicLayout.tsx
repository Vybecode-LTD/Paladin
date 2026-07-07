import { Outlet, Link, NavLink } from "react-router-dom";
import FlowBackground from "@/components/FlowBackground";
import Brandmark from "@/components/Brandmark";

const nav = [
  { to: "/product", label: "Product" },
  { to: "/how-it-works", label: "How It Works" },
  { to: "/about", label: "About" },
  { to: "/blog", label: "Blog" },
];

export default function PublicLayout() {
  return (
    <>
      <FlowBackground />
      <header style={{
        position: "sticky", top: 0, zIndex: 50,
        background: "var(--glass-bg)",
        backdropFilter: "blur(16px) saturate(160%)",
        WebkitBackdropFilter: "blur(16px) saturate(160%)",
        borderBottom: "1px solid var(--glass-border)",
        boxShadow: "var(--shadow-depth-1)",
      }}>
        <div className="container" style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          height: 68,
        }}>
          <Link to="/" style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 700 }}>
            <Brandmark size={26} />
            <span>Ashford&nbsp;&&nbsp;Briggs</span>
          </Link>
          <nav style={{ display: "flex", gap: 28, alignItems: "center" }}>
            {nav.map((n) => (
              <NavLink key={n.to} to={n.to} style={({ isActive }) => ({
                color: isActive ? "var(--accent-bright)" : "var(--text-muted)",
                fontSize: 15, fontWeight: 500,
              })}>
                {n.label}
              </NavLink>
            ))}
            <Link to="/contact" className="btn btn-primary" style={{ padding: "9px 18px" }}>
              Request a Demo
            </Link>
          </nav>
        </div>
      </header>

      <main><Outlet /></main>

      <footer style={{ borderTop: "1px solid var(--border)", padding: "56px 0 40px", marginTop: 80 }}>
        <div className="container" style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: 40 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 700, marginBottom: 12 }}>
              <Brandmark size={22} />
              Ashford & Briggs
            </div>
            <p style={{ color: "var(--text-dim)", fontSize: 14, maxWidth: 320 }}>
              Real-time AI intelligence for recruiting calls. Built by recruiters in
              Jacksonville, FL.
            </p>
          </div>
          <div>
            <h4 style={{ fontSize: 13, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: 14, letterSpacing: "0.06em" }}>Product</h4>
            {nav.map((n) => (
              <Link key={n.to} to={n.to} style={{ display: "block", color: "var(--text-muted)", fontSize: 14, marginBottom: 8 }}>{n.label}</Link>
            ))}
          </div>
          <div>
            <h4 style={{ fontSize: 13, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: 14, letterSpacing: "0.06em" }}>Contact</h4>
            <a href="mailto:inquiries@ashfordbriggs.com" style={{ display: "block", color: "var(--text-muted)", fontSize: 14, marginBottom: 8 }}>inquiries@ashfordbriggs.com</a>
            <a href="https://linkedin.com/company/ashford-briggs-llc" style={{ display: "block", color: "var(--text-muted)", fontSize: 14 }}>LinkedIn</a>
          </div>
        </div>
        <div className="container" style={{ marginTop: 40, paddingTop: 24, borderTop: "1px solid var(--border)", color: "var(--text-dim)", fontSize: 13 }}>
          © 2026 Ashford & Briggs LLC. All rights reserved.
        </div>
      </footer>
    </>
  );
}
