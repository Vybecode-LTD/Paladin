const GLYPHS = ["blue", "violet", "cyan", "amber", "coral"];

/** Deterministically hash a tag into the site's 5-hue glyph palette so
 * recurring categories become visually distinguishable, instead of every
 * tag hardcoding the same blue chip. */
export function tagGlyph(tag: string): string {
  let hash = 0;
  for (let i = 0; i < tag.length; i++) hash = (hash * 31 + tag.charCodeAt(i)) >>> 0;
  return GLYPHS[hash % GLYPHS.length];
}

/** Rough reading-time estimate from markdown source (~200 wpm). */
export function readTime(markdown: string): string {
  const words = markdown.trim().split(/\s+/).filter(Boolean).length;
  const minutes = Math.max(1, Math.round(words / 200));
  return `${minutes} min read`;
}
