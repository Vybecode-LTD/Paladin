import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";
import Seo from "@/components/Seo";
import MarkdownImage from "@/components/MarkdownImage";
import TextScrim from "@/components/TextScrim";
import { tagGlyph, readTime } from "@/lib/tagColor";
import { svgToDataUri } from "@/lib/svg";

interface Post {
  title: string; body_markdown: string; cover_image_url: string;
  cover_image_svg: string;
  tags: string; published_at: string | null;
  seo_title: string; seo_description: string; excerpt: string;
}

function SkeletonArticle() {
  return (
    <div className="container" style={{ maxWidth: 680, padding: "70px 24px 60px" }}>
      <div style={{ width: 120, height: 14, borderRadius: 4, background: "var(--bg-elevated)", marginBottom: 32 }} />
      <div style={{ width: "80%", height: 40, borderRadius: 6, background: "var(--bg-elevated)", marginBottom: 16 }} />
      <div style={{ width: 160, height: 14, borderRadius: 4, background: "var(--bg-elevated)", marginBottom: 32 }} />
      <div style={{ width: "100%", height: 320, borderRadius: "var(--radius)", background: "var(--bg-elevated)", marginBottom: 36 }} />
      {[100, 95, 88, 92].map((w, i) => (
        <div key={i} style={{ width: `${w}%`, height: 16, borderRadius: 4, background: "var(--bg-elevated)", marginBottom: 12 }} />
      ))}
    </div>
  );
}

export default function BlogPost() {
  const { slug } = useParams();
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!slug) return;
    api.get(`/blog/posts/${slug}`)
      .then(setPost)
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) return <SkeletonArticle />;
  if (notFound || !post) return (
    <div className="container" style={{ padding: 80, textAlign: "center" }}>
      <h1 style={{ fontSize: 28, marginBottom: 16 }}>Post not found</h1>
      <Link to="/blog" className="btn btn-ghost">← Back to blog</Link>
    </div>
  );

  const seoDescription = post.seo_description || post.excerpt;
  const coverSrc = post.cover_image_svg ? svgToDataUri(post.cover_image_svg) : post.cover_image_url;

  return (
    <>
      <Seo
        title={`${post.seo_title || post.title} | Ashford & Briggs`}
        description={seoDescription}
        path={`/blog/${slug}`}
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "BlogPosting",
          headline: post.seo_title || post.title,
          datePublished: post.published_at || undefined,
          description: seoDescription,
        }}
      />
      <article className="container" style={{ maxWidth: 680, padding: "70px 24px 60px" }}>
        <Link to="/blog" style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "var(--text-muted)", fontSize: 14, marginBottom: 32 }}>
          <ArrowLeft size={16} aria-hidden="true" /> Back to blog
        </Link>
        <TextScrim>
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
            {post.tags && (
              <div style={{ display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" }}>
                {post.tags.split(",").filter(Boolean).map((t) => {
                  const g = tagGlyph(t.trim());
                  return (
                    <span key={t} style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: `var(--glyph-${g})`, background: `var(--glyph-${g}-bg)`, padding: "4px 10px", borderRadius: 6 }}>{t.trim()}</span>
                  );
                })}
              </div>
            )}
            <h1 style={{ fontSize: "clamp(30px, 5vw, 46px)", fontWeight: 800, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 16 }}>{post.title}</h1>
            {post.published_at && (
              <p style={{ color: "var(--text-dim)", fontSize: 14, fontFamily: "var(--font-mono)", marginBottom: 32 }}>
                {new Date(post.published_at).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}
                {" · "}{readTime(post.body_markdown)}
              </p>
            )}
            {coverSrc && (
              <img src={coverSrc} alt={post.title} style={{ width: "100%", borderRadius: "var(--radius)", marginBottom: 36, border: "1px solid var(--border)", boxShadow: "var(--shadow-depth-2)" }} />
            )}
            <div className="prose">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ img: MarkdownImage }}>
                {post.body_markdown}
              </ReactMarkdown>
            </div>
          </motion.div>
        </TextScrim>
      </article>
    </>
  );
}
