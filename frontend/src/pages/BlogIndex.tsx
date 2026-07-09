import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { tagGlyph } from "@/lib/tagColor";
import Seo from "@/components/Seo";

interface PostItem {
  id: string; title: string; slug: string; excerpt: string;
  cover_image_url: string; tags: string; published_at: string | null;
}

const fadeUp = {
  initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

function SkeletonCard({ featured = false }: { featured?: boolean }) {
  return (
    <div className="card" style={{ gridColumn: featured ? "span 2" : undefined }}>
      <div style={{ width: "100%", height: featured ? 260 : 180, borderRadius: "var(--radius-sm)", marginBottom: 16, background: "var(--bg-elevated)" }} />
      <div style={{ width: "60%", height: 14, borderRadius: 4, background: "var(--bg-elevated)", marginBottom: 10 }} />
      <div style={{ width: "90%", height: 20, borderRadius: 4, background: "var(--bg-elevated)", marginBottom: 8 }} />
      <div style={{ width: "70%", height: 14, borderRadius: 4, background: "var(--bg-elevated)" }} />
    </div>
  );
}

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
    <>
      <Seo
        title="Blog | Ashford & Briggs"
        description="Field notes on recruiting and AI from the team building Paladin, real-time intelligence for recruiter phone calls."
        path="/blog"
      />
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
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 24 }}>
            <SkeletonCard featured />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : posts.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "60px 20px" }}>
            <p style={{ color: "var(--text-muted)" }}>No posts published yet. Check back soon.</p>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 24 }}>
            {posts.map((p, i) => {
              const featured = i === 0;
              return (
                <motion.div key={p.id} {...fadeUp} transition={{ duration: 0.4, delay: i * 0.05 }}
                  style={{ gridColumn: featured ? "span 2" : undefined }}>
                  <Link to={`/blog/${p.slug}`} className="card card-interactive"
                    style={{
                      display: featured ? "grid" : "block", height: "100%",
                      gridTemplateColumns: featured ? "1.1fr 1fr" : undefined, gap: featured ? 24 : 0,
                      boxShadow: featured ? "var(--shadow-depth-3), inset 0 1px 0 var(--glass-highlight)" : undefined,
                      borderColor: featured ? "var(--border-bright)" : undefined,
                    }}>
                    {p.cover_image_url && (
                      <img src={p.cover_image_url} alt="" style={{ width: "100%", height: featured ? "100%" : 180, minHeight: featured ? 200 : undefined, objectFit: "cover", borderRadius: "var(--radius-sm)", marginBottom: featured ? 0 : 16, border: "1px solid var(--border)" }} />
                    )}
                    <div>
                      {p.tags && (
                        <div style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap" }}>
                          {p.tags.split(",").filter(Boolean).slice(0, 3).map((t) => {
                            const g = tagGlyph(t.trim());
                            return (
                              <span key={t} style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: `var(--glyph-${g})`, background: `var(--glyph-${g}-bg)`, padding: "3px 8px", borderRadius: 6 }}>{t.trim()}</span>
                            );
                          })}
                        </div>
                      )}
                      <h3 style={{
                        fontSize: featured ? 26 : 20, fontWeight: 700, marginBottom: 8,
                        display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden",
                      }}>{p.title}</h3>
                      <p style={{
                        color: "var(--text-muted)", fontSize: featured ? 16 : 15,
                        display: "-webkit-box", WebkitLineClamp: featured ? 3 : 2, WebkitBoxOrient: "vertical", overflow: "hidden",
                      }}>{p.excerpt}</p>
                      {p.published_at && (
                        <p style={{ color: "var(--text-dim)", fontSize: 13, marginTop: 14, fontFamily: "var(--font-mono)" }}>
                          {new Date(p.published_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })}
                        </p>
                      )}
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        )}
      </section>
    </>
  );
}
