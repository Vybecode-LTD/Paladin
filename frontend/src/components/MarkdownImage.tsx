// Custom renderer for react-markdown's `img` node. Markdown's optional
// "title" (the quoted string after the URL: `![alt](url "caption")`) is
// repurposed as a visible caption, rendered as a proper <figure>/<figcaption>
// instead of the browser's native (and inconsistent) title tooltip.
export default function MarkdownImage({ src, alt, title }: { src?: string; alt?: string; title?: string }) {
  if (!src) return null;
  return (
    <figure style={{ margin: "28px 0" }}>
      <img src={src} alt={alt || ""} style={{ width: "100%", borderRadius: "var(--radius)", display: "block" }} />
      {title && (
        <figcaption style={{ fontSize: 13, color: "var(--text-dim)", textAlign: "center", marginTop: 8, fontStyle: "italic" }}>
          {title}
        </figcaption>
      )}
    </figure>
  );
}
