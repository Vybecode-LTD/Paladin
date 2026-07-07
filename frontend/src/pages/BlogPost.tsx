import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";

interface Post {
  title: string; body_markdown: string; cover_image_url: string;
  tags: string; published_at: string | null;
  seo_title: string; seo_description: string;
}

export default function BlogPost() {
  const { slug } = useParams();
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!slug) return;
    api.get(`/blog/posts/${slug}`)
      .then((p) => {
        setPost(p);
        // Simple client-side SEO: set document title/description.
        document.title = (p.seo_title || p.title) + " | Ashford & Briggs";
        const meta = document.querySelector('meta[name="description"]');
        if (meta && p.seo_description) meta.setAttribute("content", p.seo_description);
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) return <div className="container" style={{ padding: 80, color: "var(--text-dim)" }}>Loading…</div>;
  if (notFound || !post) return (
    <div className="container" style={{ padding: 80, textAlign: "center" }}>
      <h1 style={{ fontSize: 28, marginBottom: 16 }}>Post not found</h1>
      <Link to="/blog" className="btn btn-ghost">← Back to blog</Link>
    </div>
  );

  return (
    <article className="container" style={{ maxWidth: 760, padding: "70px 24px 60px" }}>
      <Link to="/blog" style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "var(--text-muted)", fontSize: 14, marginBottom: 32 }}>
        <ArrowLeft size={16} /> Back to blog
      </Link>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        {post.tags && (
          <div style={{ display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" }}>
            {post.tags.split(",").filter(Boolean).map((t) => (
              <span key={t} style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--glyph-blue)", background: "var(--glyph-blue-bg)", padding: "4px 10px", borderRadius: 6 }}>{t.trim()}</span>
            ))}
          </div>
        )}
        <h1 style={{ fontSize: "clamp(30px, 5vw, 46px)", fontWeight: 800, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 16 }}>{post.title}</h1>
        {post.published_at && (
          <p style={{ color: "var(--text-dim)", fontSize: 14, fontFamily: "var(--font-mono)", marginBottom: 32 }}>
            {new Date(post.published_at).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}
          </p>
        )}
        {post.cover_image_url && (
          <img src={post.cover_image_url} alt="" style={{ width: "100%", borderRadius: "var(--radius)", marginBottom: 36 }} />
        )}
        <div className="prose">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{post.body_markdown}</ReactMarkdown>
        </div>
      </motion.div>
    </article>
  );
}
