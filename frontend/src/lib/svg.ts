// Render an SVG string as an <img src>. Using a data URI (rather than
// dangerouslySetInnerHTML) is deliberate: an SVG loaded via <img> runs in the
// browser's "secure static mode" — no script execution, no external fetches —
// so admin-authored / AI-generated headers can't become an XSS vector.
// encodeURIComponent (not base64) keeps it readable and correctly escapes the
// `#` in hex colors, `<`, `>`, and quotes.
export function svgToDataUri(svg: string): string {
  return `data:image/svg+xml,${encodeURIComponent(svg)}`;
}
