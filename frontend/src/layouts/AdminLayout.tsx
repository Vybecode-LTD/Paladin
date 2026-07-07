import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { LayoutDashboard, FileText, Inbox, LogOut } from "lucide-react";
import Brandmark from "@/components/Brandmark";

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const nav = useNavigate();

  const items = [
    { to: "/admin", label: "Dashboard", icon: LayoutDashboard, min: "author" },
    { to: "/admin/posts", label: "Posts", icon: FileText, min: "author" },
    { to: "/admin/demo-requests", label: "Demo Inbox", icon: Inbox, min: "editor" },
  ];
  const rank: Record<string, number> = { author: 1, editor: 2, admin: 3 };
  const visible = items.filter((i) => rank[user!.role] >= rank[i.min]);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg)" }}>
      <aside style={{
        width: 240, borderRight: "1px solid var(--border)", padding: "24px 16px",
        display: "flex", flexDirection: "column", background: "var(--bg-elevated)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 700, padding: "0 8px 24px" }}>
          <Brandmark size={22} /> Admin
        </div>
        <nav style={{ display: "flex", flexDirection: "column", gap: 4, flex: 1 }}>
          {visible.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end style={({ isActive }) => ({
              display: "flex", alignItems: "center", gap: 12, padding: "10px 12px",
              borderRadius: 10, fontSize: 14, fontWeight: 500,
              background: isActive ? "var(--bg-card)" : "transparent",
              color: isActive ? "var(--accent-bright)" : "var(--text-muted)",
            })}>
              <Icon size={18} /> {label}
            </NavLink>
          ))}
        </nav>
        <div style={{ borderTop: "1px solid var(--border)", paddingTop: 16 }}>
          <div style={{ fontSize: 13, color: "var(--text-muted)", padding: "0 8px 4px" }}>{user!.full_name || user!.email}</div>
          <div style={{ fontSize: 12, color: "var(--accent)", padding: "0 8px 12px", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>{user!.role}</div>
          <button onClick={() => { logout(); nav("/admin/login"); }} className="btn btn-ghost" style={{ width: "100%", justifyContent: "center", padding: "9px" }}>
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </aside>
      <div style={{ flex: 1, padding: "32px 40px", overflowY: "auto" }}>
        <Outlet />
      </div>
    </div>
  );
}
