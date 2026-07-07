import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Circle, CheckCircle2, Trash2, Copy, Check } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

interface PostItem {
  id: string; title: string; slug: string; status: string;
  published_at: string | null; created_at: string;
}

export default function PostList() {
  const { user } = useAuth();
  const canDelete = user?.role === "editor" || user?.role === "admin";
  const [posts, setPosts] = useState<PostItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    api.get("/admin/posts").then(setPosts).catch(() => {}).finally(() => setLoading(false));
  }, []);

  async function handleDelete(e: React.MouseEvent, id: string, title: string) {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm(`Delete "${title}"? This can't be undone.`)) return;
    try {
      await api.del(`/admin/posts/${id}`);
      setPosts((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      alert(err instanceof Error ? err.message : "Delete failed");
    }
  }

  async function handleCopyUrl(e: React.MouseEvent, p: PostItem) {
    e.preventDefault();
    e.stopPropagation();
    const url = p.status === "published"
      ? `https://ashfordbriggs.com/blog/${p.slug}`
      : p.slug;
    try {
      await navigator.clipboard.writeText(url);
      setCopiedId(p.id);
      setTimeout(() => setCopiedId((prev) => (prev === p.id ? null : prev)), 1500);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Copy failed");
    }
  }

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
              style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 20px", borderBottom: "1px solid var(--border)", flexWrap: "wrap", gap: 10 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 0 }}>
                {p.status === "published"
                  ? <CheckCircle2 size={16} color="var(--success)" />
                  : <Circle size={16} color="var(--text-dim)" />}
                <span style={{ fontWeight: 600, overflowWrap: "anywhere" }}>{p.title}</span>
                <button onClick={(e) => handleCopyUrl(e, p)} className="btn btn-ghost"
                  style={{ padding: "6px 10px", borderColor: "transparent" }}
                  title={p.status === "published" ? "Copy blog URL" : "Copy slug (not published yet)"}>
                  {copiedId === p.id
                    ? <Check size={16} color="var(--success)" />
                    : <Copy size={16} />}
                </button>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
                <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", textTransform: "uppercase", color: p.status === "published" ? "var(--success)" : "var(--text-dim)" }}>{p.status}</span>
                <span style={{ fontSize: 13, color: "var(--text-dim)" }}>{new Date(p.published_at || p.created_at).toLocaleDateString()}</span>
                {canDelete && (
                  <button onClick={(e) => handleDelete(e, p.id, p.title)} className="btn btn-ghost"
                    style={{ padding: "6px 10px", borderColor: "transparent" }} title="Delete post">
                    <Trash2 size={16} color="var(--danger)" />
                  </button>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
