import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import {
  LayoutDashboard, FileText, Inbox, LogOut, Users as UsersIcon, Menu, X,
  Settings as SettingsIcon, UserCircle,
} from "lucide-react";
import Brandmark from "@/components/Brandmark";

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const items = [
    { to: "/admin", label: "Dashboard", icon: LayoutDashboard, min: "author" },
    { to: "/admin/posts", label: "Posts", icon: FileText, min: "author" },
    { to: "/admin/demo-requests", label: "Demo Inbox", icon: Inbox, min: "editor" },
    { to: "/admin/users", label: "Users", icon: UsersIcon, min: "admin" },
    { to: "/admin/settings", label: "Settings", icon: SettingsIcon, min: "admin" },
  ];
  const rank: Record<string, number> = { author: 1, editor: 2, admin: 3 };
  const visible = items.filter((i) => rank[user!.role] >= rank[i.min]);

  return (
    <div className="admin-shell">
      <button
        className="admin-menu-btn"
        aria-label={menuOpen ? "Close menu" : "Open menu"}
        onClick={() => setMenuOpen((o) => !o)}
      >
        {menuOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {menuOpen && <div className="admin-scrim" onClick={() => setMenuOpen(false)} />}

      <aside className={`admin-sidebar${menuOpen ? " admin-sidebar-open" : ""}`}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 700, padding: "0 8px 24px" }}>
          <Brandmark size={22} /> Admin
        </div>
        <nav style={{ display: "flex", flexDirection: "column", gap: 4, flex: 1 }}>
          {visible.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end onClick={() => setMenuOpen(false)} style={({ isActive }) => ({
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
          <NavLink to="/admin/profile" onClick={() => setMenuOpen(false)} style={({ isActive }) => ({
            display: "flex", alignItems: "center", gap: 8, padding: "0 8px 4px",
            fontSize: 13, color: isActive ? "var(--accent-bright)" : "var(--text-muted)",
            textDecoration: "none",
          })}>
            <UserCircle size={15} /> {user!.full_name || user!.email}
          </NavLink>
          <div style={{ fontSize: 12, color: "var(--accent)", padding: "0 8px 12px", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>{user!.role}</div>
          <button onClick={() => { logout(); nav("/admin/login"); }} className="btn btn-ghost" style={{ width: "100%", justifyContent: "center", padding: "9px" }}>
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </aside>
      <div className="admin-content">
        <Outlet />
      </div>
    </div>
  );
}
