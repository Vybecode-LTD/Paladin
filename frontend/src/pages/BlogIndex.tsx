import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { api } from "@/lib/api";

interface PostItem {
  id: string; title: string; slug: string; excerpt: string;
  cover_image_url: string; tags: string; published_at: string | null;
}

const fadeUp = {
  initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

export default function BlogIndex() {
  const [posts, setPosts] = useState<PostItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/blog/posts")
      .then(setPosts)
      .catch(() => setPosts([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section style={{ padding: "90px 0 60px" }} className="container">
      <motion.div {...fadeUp} style={{ maxWidth: 680, marginBottom: 48 }}>
        <span className="eyebrow">Blog</span>
        <h1 style={{ fontSize: "clamp(34px, 5vw, 56px)", fontWeight: 800, letterSpacing: "-0.03em", margin: "16px 0 16px" }}>
          Field notes on <span className="gradient-text">recruiting & AI.</span>
        </h1>
        <p style={{ fontSize: 18, color: "var(--text-muted)" }}>
          Ideas on hiring in the age of generative AI — from the team building Paladin.
        </p>
      </motion.div>

      {loading ? (
        <p style={{ color: "var(--text-dim)" }}>Loading posts…</p>
      ) : posts.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "60px 20px" }}>
          <p style={{ color: "var(--text-muted)" }}>No posts published yet. Check back soon.</p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 24 }}>
          {posts.map((p, i) => (
            <motion.div key={p.id} {...fadeUp} transition={{ duration: 0.4, delay: i * 0.05 }}>
              <Link to={`/blog/${p.slug}`} className="card" style={{ display: "block", height: "100%" }}>
                {p.cover_image_url && (
                  <img src={p.cover_image_url} alt="" style={{ width: "100%", height: 180, objectFit: "cover", borderRadius: "var(--radius-sm)", marginBottom: 16 }} />
                )}
                {p.tags && (
                  <div style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap" }}>
                    {p.tags.split(",").filter(Boolean).slice(0, 3).map((t) => (
                      <span key={t} style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--glyph-blue)", background: "var(--glyph-blue-bg)", padding: "3px 8px", borderRadius: 6 }}>{t.trim()}</span>
                    ))}
                  </div>
                )}
                <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>{p.title}</h3>
                <p style={{ color: "var(--text-muted)", fontSize: 15 }}>{p.excerpt}</p>
                {p.published_at && (
                  <p style={{ color: "var(--text-dim)", fontSize: 13, marginTop: 14, fontFamily: "var(--font-mono)" }}>
                    {new Date(p.published_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })}
                  </p>
                )}
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </section>
  );
}
