import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Circle, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

interface PostItem {
  id: string; title: string; slug: string; status: string;
  updated_at: string; created_at: string;
}

export default function PostList() {
  const [posts, setPosts] = useState<PostItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/admin/posts").then(setPosts).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
        <h1 style={{ fontSize: 30, fontWeight: 800 }}>Posts</h1>
        <Link to="/admin/posts/new" className="btn btn-primary"><Plus size={18} /> New post</Link>
      </div>

      {loading ? <p style={{ color: "var(--text-dim)" }}>Loading…</p> : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          {posts.length === 0 ? (
            <p style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>No posts yet. Create your first one.</p>
          ) : posts.map((p) => (
            <Link key={p.id} to={`/admin/posts/${p.id}`}
              style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                {p.status === "published"
                  ? <CheckCircle2 size={16} color="var(--success)" />
                  : <Circle size={16} color="var(--text-dim)" />}
                <span style={{ fontWeight: 600 }}>{p.title}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", textTransform: "uppercase", color: p.status === "published" ? "var(--success)" : "var(--text-dim)" }}>{p.status}</span>
                <span style={{ fontSize: 13, color: "var(--text-dim)" }}>{new Date(p.updated_at).toLocaleDateString()}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
