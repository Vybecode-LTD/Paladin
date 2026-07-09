import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Sparkles, Save, Send, Wand2, Loader2, Eye, Code, ImagePlus, EyeOff } from "lucide-react";
import { api, aiApi } from "@/lib/api";
import MarkdownImage from "@/components/MarkdownImage";
import Waveform from "@/components/Waveform";

const inputStyle: React.CSSProperties = {
  width: "100%", padding: "11px 13px", background: "var(--bg)",
  border: "1px solid var(--border-bright)", borderRadius: "var(--radius-sm)",
  color: "var(--text)", fontSize: 15, fontFamily: "var(--font-sans)",
};
const labelStyle: React.CSSProperties = {
  fontSize: 13, color: "var(--text-muted)", display: "block", marginBottom: 6,
};

interface PostState {
  title: string; body_markdown: string; excerpt: string; tags: string;
  cover_image_url: string; seo_title: string; seo_description: string;
  status: "draft" | "published";
}

const EMPTY: PostState = {
  title: "", body_markdown: "", excerpt: "", tags: "",
  cover_image_url: "", seo_title: "", seo_description: "", status: "draft",
};

export default function PostEditor() {
  const { id } = useParams();
  const nav = useNavigate();
  const isNew = !id;

  const [post, setPost] = useState<PostState>(EMPTY);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [view, setView] = useState<"write" | "preview">("write");
  const bodyRef = useRef<HTMLTextAreaElement>(null);

  // AI panel state
  const [aiTopic, setAiTopic] = useState("");
  const [aiTone, setAiTone] = useState("professional");
  const [aiLength, setAiLength] = useState("medium");
  const [aiBusy, setAiBusy] = useState<string | null>(null);
  const [titleIdeas, setTitleIdeas] = useState<string>("");

  useEffect(() => {
    if (isNew) return;
    api.get(`/admin/posts/${id}`)
      .then((p) => setPost({
        title: p.title, body_markdown: p.body_markdown, excerpt: p.excerpt,
        tags: p.tags, cover_image_url: p.cover_image_url, seo_title: p.seo_title,
        seo_description: p.seo_description, status: p.status,
      }))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id, isNew]);

  const upd = (k: keyof PostState) => (v: string) => setPost((p) => ({ ...p, [k]: v }));

  // ---- AI actions (call our backend proxy; key stays server-side) ----
  async function genDraft() {
    if (!aiTopic.trim()) return;
    setAiBusy("draft");
    try {
      const { result } = await aiApi.draft(aiTopic, aiTone, aiLength);
      setPost((p) => ({ ...p, body_markdown: result }));
      setView("write");
    } catch (e) { alert(e instanceof Error ? e.message : "Draft failed"); }
    finally { setAiBusy(null); }
  }
  async function genTitles() {
    if (!aiTopic.trim()) return;
    setAiBusy("titles");
    try { const { result } = await aiApi.titles(aiTopic); setTitleIdeas(result); }
    catch (e) { alert(e instanceof Error ? e.message : "Titles failed"); }
    finally { setAiBusy(null); }
  }
  async function genExcerpt() {
    if (!post.body_markdown.trim()) return alert("Write or generate a body first.");
    setAiBusy("excerpt");
    try { const { result } = await aiApi.excerpt(post.body_markdown); upd("excerpt")(result.trim()); }
    catch (e) { alert(e instanceof Error ? e.message : "Excerpt failed"); }
    finally { setAiBusy(null); }
  }
  async function genSeo() {
    if (!post.title.trim()) return alert("Add a title first.");
    setAiBusy("seo");
    try {
      const { result } = await aiApi.seo(post.title, post.body_markdown);
      const parsed = JSON.parse(result.replace(/```json|```/g, "").trim());
      setPost((p) => ({ ...p, seo_title: parsed.seo_title || p.seo_title, seo_description: parsed.seo_description || p.seo_description }));
    } catch (e) { alert(e instanceof Error ? e.message : "SEO generation failed"); }
    finally { setAiBusy(null); }
  }

  // ---- Insert image (alt text and the visible caption are separate — alt
  // describes the image for screen readers, caption is visible body copy) ----
  function insertImage() {
    const url = window.prompt("Image URL:");
    if (!url || !url.trim()) return;
    const alt = window.prompt("Alt text (describes the image — required for accessibility):");
    if (!alt || !alt.trim()) { alert("Alt text is required."); return; }
    const caption = window.prompt("Caption (optional, shown under the image):") || "";
    // Markdown's optional quoted "title" after the URL becomes the figure
    // caption — see MarkdownImage.tsx's custom img renderer.
    const snippet = caption
      ? `![${alt.trim()}](${url.trim()} "${caption.replace(/"/g, "'")}")`
      : `![${alt.trim()}](${url.trim()})`;

    const textarea = bodyRef.current;
    if (!textarea) {
      upd("body_markdown")(`${post.body_markdown}\n\n${snippet}\n\n`);
      return;
    }
    const { selectionStart, selectionEnd } = textarea;
    const before = post.body_markdown.slice(0, selectionStart);
    const after = post.body_markdown.slice(selectionEnd);
    const insertion = `\n\n${snippet}\n\n`;
    upd("body_markdown")(before + insertion + after);
    setView("write");
    setTimeout(() => {
      textarea.focus();
      const pos = before.length + insertion.length;
      textarea.setSelectionRange(pos, pos);
    }, 0);
  }

  // ---- Save / publish / unpublish ----
  async function save(statusOverride?: "draft" | "published") {
    if (!post.title.trim()) return alert("A title is required.");
    setSaving(true);
    const payload = { ...post, status: statusOverride ?? post.status };
    try {
      if (isNew) {
        const created = await api.post("/admin/posts", payload);
        nav(`/admin/posts/${created.id}`);
      } else {
        await api.patch(`/admin/posts/${id}`, payload);
        setPost((p) => ({ ...p, status: payload.status as PostState["status"] }));
      }
    } catch (e) { alert(e instanceof Error ? e.message : "Save failed"); }
    finally { setSaving(false); }
  }

  function unpublish() {
    if (!window.confirm("Unpublish this post? It will no longer be visible on the public blog.")) return;
    save("draft");
  }

  if (loading) return <p style={{ color: "var(--text-dim)" }}>Loading…</p>;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <h1 style={{ fontSize: 26, fontWeight: 800 }}>{isNew ? "New Post" : "Edit Post"}</h1>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button onClick={() => save()} disabled={saving} className="btn btn-ghost">
            {saving ? <Loader2 size={16} className="spin" aria-hidden="true" /> : <Save size={16} aria-hidden="true" />}
            {post.status === "published" ? "Save changes" : "Save draft"}
          </button>
          {!isNew && post.status === "published" && (
            <button onClick={unpublish} disabled={saving} className="btn btn-ghost">
              <EyeOff size={16} aria-hidden="true" /> Unpublish
            </button>
          )}
          <button onClick={() => save("published")} disabled={saving} className="btn btn-primary">
            <Send size={16} aria-hidden="true" /> {post.status === "published" ? "Update" : "Publish"}
          </button>
        </div>
      </div>

      <div className="admin-editor-grid" style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 24, alignItems: "start" }}>
        {/* Main editor column */}
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <div>
            <label style={labelStyle}>Title</label>
            <input style={{ ...inputStyle, fontSize: 20, fontWeight: 700 }} value={post.title}
              onChange={(e) => upd("title")(e.target.value)} placeholder="Post title" />
          </div>

          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <label style={labelStyle}>Body (Markdown)</label>
              <div style={{ display: "flex", gap: 4 }}>
                <button onClick={insertImage} className="btn btn-ghost" style={{ padding: "5px 10px", fontSize: 13 }}>
                  <ImagePlus size={14} /> Insert image
                </button>
                <button onClick={() => setView("write")} className="btn btn-ghost" style={{ padding: "5px 10px", fontSize: 13, borderColor: view === "write" ? "var(--accent)" : undefined }}>
                  <Code size={14} /> Write
                </button>
                <button onClick={() => setView("preview")} className="btn btn-ghost" style={{ padding: "5px 10px", fontSize: 13, borderColor: view === "preview" ? "var(--accent)" : undefined }}>
                  <Eye size={14} /> Preview
                </button>
              </div>
            </div>
            {view === "write" ? (
              <textarea ref={bodyRef} style={{ ...inputStyle, minHeight: 460, fontFamily: "var(--font-mono)", fontSize: 14, lineHeight: 1.7, resize: "vertical" }}
                value={post.body_markdown} onChange={(e) => upd("body_markdown")(e.target.value)}
                placeholder="Write in Markdown, or generate a draft with the AI panel →" />
            ) : (
              <div className="card prose" style={{ minHeight: 460 }}>
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ img: MarkdownImage }}>
                  {post.body_markdown || "*Nothing to preview yet.*"}
                </ReactMarkdown>
              </div>
            )}
          </div>

          <div className="admin-grid-2col" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <div>
              <label style={labelStyle}>Tags (comma-separated)</label>
              <input style={inputStyle} value={post.tags} onChange={(e) => upd("tags")(e.target.value)} placeholder="hiring, ai, recruiting" />
            </div>
            <div>
              <label style={labelStyle}>Cover image URL</label>
              <input style={inputStyle} value={post.cover_image_url} onChange={(e) => upd("cover_image_url")(e.target.value)} placeholder="https://…" />
            </div>
          </div>

          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <label style={labelStyle}>Excerpt</label>
              <button onClick={genExcerpt} disabled={aiBusy === "excerpt"} className="btn btn-ghost" style={{ padding: "4px 10px", fontSize: 12 }}>
                {aiBusy === "excerpt" ? <Waveform size="thin" bars={5} onLight /> : <Wand2 size={13} aria-hidden="true" />} Generate
              </button>
            </div>
            <textarea style={{ ...inputStyle, minHeight: 70, resize: "vertical" }} value={post.excerpt} onChange={(e) => upd("excerpt")(e.target.value)} />
          </div>

          {/* SEO */}
          <div className="card" style={{ background: "var(--bg-elevated)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <h4 style={{ fontSize: 14, fontWeight: 700 }}>SEO metadata</h4>
              <button onClick={genSeo} disabled={aiBusy === "seo"} className="btn btn-ghost" style={{ padding: "4px 10px", fontSize: 12 }}>
                {aiBusy === "seo" ? <Waveform size="thin" bars={5} onLight /> : <Wand2 size={13} aria-hidden="true" />} Auto-generate
              </button>
            </div>
            <label style={labelStyle}>SEO title</label>
            <input style={{ ...inputStyle, marginBottom: 12 }} value={post.seo_title} onChange={(e) => upd("seo_title")(e.target.value)} />
            <label style={labelStyle}>SEO description</label>
            <textarea style={{ ...inputStyle, minHeight: 60, resize: "vertical" }} value={post.seo_description} onChange={(e) => upd("seo_description")(e.target.value)} />
          </div>
        </div>

        {/* AI assist panel */}
        <div className="card admin-ai-panel" style={{ position: "sticky", top: 24, background: "linear-gradient(160deg, var(--bg-card), rgba(0,118,209,0.1))" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
            <Sparkles size={18} color="var(--accent-bright)" />
            <h3 style={{ fontSize: 16, fontWeight: 700 }}>AI Assistant</h3>
          </div>
          <p style={{ fontSize: 13, color: "var(--text-dim)", marginBottom: 16 }}>
            Generate a full draft, brainstorm titles, or fill in excerpt & SEO.
            Runs through the secure backend proxy.
          </p>

          <label style={labelStyle}>Topic / brief</label>
          <textarea style={{ ...inputStyle, minHeight: 76, resize: "vertical", marginBottom: 12 }} value={aiTopic}
            onChange={(e) => setAiTopic(e.target.value)} placeholder="e.g. Why résumé screening is broken in the age of generative AI" />

          <div className="admin-grid-2col" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
            <div>
              <label style={labelStyle}>Tone</label>
              <select style={inputStyle} value={aiTone} onChange={(e) => setAiTone(e.target.value)}>
                <option value="professional">Professional</option>
                <option value="conversational">Conversational</option>
                <option value="authoritative">Authoritative</option>
                <option value="punchy">Punchy</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>Length</label>
              <select style={inputStyle} value={aiLength} onChange={(e) => setAiLength(e.target.value)}>
                <option value="short">Short</option>
                <option value="medium">Medium</option>
                <option value="long">Long</option>
              </select>
            </div>
          </div>

          <button onClick={genDraft} disabled={aiBusy === "draft" || !aiTopic.trim()} className="btn btn-primary" style={{ width: "100%", justifyContent: "center", marginBottom: 10 }}>
            {aiBusy === "draft" ? <><Waveform size="thin" bars={6} /> Writing…</> : <><Wand2 size={16} aria-hidden="true" /> Generate full draft</>}
          </button>
          <button onClick={genTitles} disabled={aiBusy === "titles" || !aiTopic.trim()} className="btn btn-ghost" style={{ width: "100%", justifyContent: "center" }}>
            {aiBusy === "titles" ? <Waveform size="thin" bars={6} onLight /> : <Sparkles size={16} aria-hidden="true" />} Brainstorm titles
          </button>

          {titleIdeas && (
            <div style={{ marginTop: 16, padding: 14, background: "var(--bg)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)" }}>
              <div className="prose" style={{ fontSize: 14 }}>
                <ReactMarkdown>{titleIdeas}</ReactMarkdown>
              </div>
              <p style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 8 }}>Click a title to copy it into the title field.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
