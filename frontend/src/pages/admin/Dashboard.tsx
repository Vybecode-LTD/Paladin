import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileText, Inbox, PenSquare, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function Dashboard() {
  const { user } = useAuth();
  const [postCount, setPostCount] = useState<number | null>(null);
  const [demoCount, setDemoCount] = useState<number | null>(null);

  useEffect(() => {
    api.get("/admin/posts").then((p) => setPostCount(p.length)).catch(() => {});
    if (user && (user.role === "editor" || user.role === "admin")) {
      api.get("/admin/demo-requests").then((d) => setDemoCount(d.length)).catch(() => {});
    }
  }, [user]);

  return (
    <div>
      <h1 style={{ fontSize: 30, fontWeight: 800, marginBottom: 4 }}>Dashboard</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 32 }}>Welcome back, {user?.full_name || user?.email}.</p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 20, marginBottom: 32 }}>
        <div className="card">
          <FileText size={22} color="var(--accent-bright)" />
          <div style={{ fontSize: 34, fontWeight: 800, marginTop: 12 }}>{postCount ?? "—"}</div>
          <p style={{ color: "var(--text-muted)", fontSize: 14 }}>Posts you can manage</p>
        </div>
        {(user?.role === "editor" || user?.role === "admin") && (
          <div className="card">
            <Inbox size={22} color="var(--accent-bright)" />
            <div style={{ fontSize: 34, fontWeight: 800, marginTop: 12 }}>{demoCount ?? "—"}</div>
            <p style={{ color: "var(--text-muted)", fontSize: 14 }}>Demo requests</p>
          </div>
        )}
      </div>

      <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
        <Link to="/admin/posts/new" className="btn btn-primary"><Sparkles size={18} /> New AI-assisted post</Link>
        <Link to="/admin/posts" className="btn btn-ghost"><PenSquare size={16} /> Manage posts</Link>
      </div>
    </div>
  );
}
