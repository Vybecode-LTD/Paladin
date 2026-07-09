"""Server-side Anthropic proxy. The API key NEVER reaches the browser —
the admin frontend calls our /api/admin/ai/* routes, which call this."""
import re
import httpx
from app.core.config import settings

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# Cap on accepted SVG size — a blog header is a few KB; anything larger is a
# runaway generation, not a header.
SVG_MAX_BYTES = 100_000


class AIServiceError(Exception):
    """Upstream Anthropic call failed — caught by routers/ai.py and turned
    into a clean 502/504 instead of an unhandled 500."""


# ---------------------------------------------------------------------------
# SVG extraction / sanitization / validation
#
# The model's output is treated as UNTRUSTED. Even though generated headers are
# rendered via <img src="data:image/svg+xml,…"> (which runs SVG in secure static
# mode — no script execution, no external fetches), we sanitize server-side too
# as defense in depth: strip <script>, event handlers, <foreignObject>, embedded
# raster/<image>, and external references before the SVG is ever persisted.
# Regex-based (no lxml/defusedxml dependency added); acceptable because the
# render path already neutralizes script and the authors are trusted (author+).
# ---------------------------------------------------------------------------

def extract_svg(text: str) -> str | None:
    """Pull the first complete <svg>…</svg> out of a model response, stripping
    any stray Markdown code fences or surrounding prose."""
    if not text:
        return None
    cleaned = re.sub(r"```(?:svg|xml|html)?", "", text, flags=re.IGNORECASE).replace("```", "")
    match = re.search(r"<svg\b.*?</svg\s*>", cleaned, flags=re.IGNORECASE | re.DOTALL)
    return match.group(0).strip() if match else None


def sanitize_svg(svg: str) -> str:
    """Remove script/interactivity/external-reference vectors from model SVG."""
    # <script>…</script> and <foreignObject>…</foreignObject> (arbitrary HTML/JS).
    svg = re.sub(r"<script\b.*?</script\s*>", "", svg, flags=re.IGNORECASE | re.DOTALL)
    svg = re.sub(r"<script\b[^>]*/\s*>", "", svg, flags=re.IGNORECASE)
    svg = re.sub(r"<foreignObject\b.*?</foreignObject\s*>", "", svg, flags=re.IGNORECASE | re.DOTALL)
    # Embedded raster / external image tags.
    svg = re.sub(r"<image\b.*?</image\s*>", "", svg, flags=re.IGNORECASE | re.DOTALL)
    svg = re.sub(r"<image\b[^>]*/?\s*>", "", svg, flags=re.IGNORECASE)
    # on*="…" / on*='…' event handlers.
    svg = re.sub(r"\s+on[a-z]+\s*=\s*\"[^\"]*\"", "", svg, flags=re.IGNORECASE)
    svg = re.sub(r"\s+on[a-z]+\s*=\s*'[^']*'", "", svg, flags=re.IGNORECASE)
    # href / xlink:href pointing anywhere external or to javascript:/data:.
    svg = re.sub(
        r"\s+(?:xlink:)?href\s*=\s*\"\s*(?:https?:|//|data:|javascript:)[^\"]*\"",
        "", svg, flags=re.IGNORECASE,
    )
    svg = re.sub(
        r"\s+(?:xlink:)?href\s*=\s*'\s*(?:https?:|//|data:|javascript:)[^']*'",
        "", svg, flags=re.IGNORECASE,
    )
    # External url(...) references inside styles/attributes (e.g. @import, remote fills).
    svg = re.sub(r"@import[^;\n]*;?", "", svg, flags=re.IGNORECASE)
    svg = re.sub(
        r"url\(\s*['\"]?\s*(?:https?:|//|javascript:)[^)]*\)",
        "none", svg, flags=re.IGNORECASE,
    )
    return svg.strip()


def validate_svg(svg: str | None) -> tuple[bool, str]:
    """Structural QC gate. Returns (ok, reason-if-not-ok)."""
    if not svg:
        return False, "No <svg> element was found in the response."
    if len(svg.encode("utf-8")) > SVG_MAX_BYTES:
        return False, "The SVG is too large."
    low = svg.lower()
    if not low.startswith("<svg") or "</svg" not in low:
        return False, "The markup is not a single well-formed <svg> element."
    if "viewbox" not in low:
        return False, "The <svg> is missing a viewBox."
    for banned in ("<script", "<foreignobject", "<image", "javascript:"):
        if banned in low:
            return False, f"The SVG still contains a disallowed '{banned}'."
    return True, ""


class AnthropicService:
    def __init__(self) -> None:
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model

    async def _call(self, system: str, user: str, max_tokens: int = 2000) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(ANTHROPIC_URL, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException:
            raise AIServiceError("The AI service timed out. Please try again.")
        except httpx.HTTPStatusError as exc:
            raise AIServiceError(
                f"AI service returned an error ({exc.response.status_code}). Please try again."
            )
        except httpx.HTTPError:
            raise AIServiceError("Could not reach the AI service. Please try again.")
        return "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )

    async def draft_post(self, topic: str, tone: str = "professional",
                         length: str = "medium") -> str:
        system = (
            "You are the content lead for Ashford & Briggs, maker of Paladin — "
            "real-time AI intelligence for recruiting phone calls. Write in a "
            "sharp, credible, human B2B voice. Paladin STRENGTHENS the human "
            "conversation; it does not replace recruiters. Output clean Markdown "
            "with a single H1, clear H2s, and a short call-to-action close."
        )
        words = {"short": "400-600", "medium": "800-1200", "long": "1500-2000"}
        user = (
            f"Write a {tone} blog post of {words.get(length, '800-1200')} words.\n"
            f"Topic: {topic}\n\n"
            "Return ONLY the Markdown body."
        )
        return await self._call(system, user, max_tokens=4000)

    async def suggest_titles(self, topic: str) -> str:
        system = ("You write punchy, specific B2B blog titles for a recruiting-"
                  "tech company. No clickbait.")
        user = (f"Give 8 title options for a post about: {topic}\n"
                "Return as a Markdown numbered list, titles only.")
        return await self._call(system, user, max_tokens=600)

    async def write_excerpt(self, body_markdown: str) -> str:
        system = "You write concise 1-2 sentence blog excerpts (under 300 chars)."
        user = f"Write an excerpt for this post:\n\n{body_markdown[:2000]}"
        return await self._call(system, user, max_tokens=200)

    async def seo_meta(self, title: str, body_markdown: str) -> str:
        system = ("You are an SEO specialist. Return a JSON object with keys "
                  "'seo_title' (<=60 chars) and 'seo_description' (<=155 chars). "
                  "Return ONLY the JSON, no fences.")
        user = f"Title: {title}\n\nBody:\n{body_markdown[:1500]}"
        return await self._call(system, user, max_tokens=300)

    # ---- Vector blog header generation (SVG, on-brand, sanitized) ----
    _STYLE_DIRECTIONS = {
        "editorial": (
            "EDITORIAL TYPOGRAPHIC. The post title is the hero: set it large "
            "(80-120px), bold (700-800), tight letter-spacing (-0.02em), ink "
            "(#1a1c1f), left-aligned, wrapped across 2-3 balanced lines using "
            "separate <text>/<tspan> lines. Above it, a small uppercase mono "
            "eyebrow (letter-spacing 0.12em) in the accent blue (#0076d1) — e.g. "
            "the primary tag or 'ASHFORD & BRIGGS'. Supporting graphics stay "
            "quiet: at most one thin accent underline or rule and a restrained "
            "geometric texture (a faint dotted grid, a few thin 'signal' lines, "
            "or a single soft off-canvas accent shape). Think a high-end "
            "magazine cover or Stripe press page — lots of negative space, one "
            "clear focal point."
        ),
        "signal": (
            "ABSTRACT SIGNAL MOTIF. No title text required. Build a minimal "
            "composition of thin waveform / network / data-flow lines in the "
            "accent blues over the near-white ground, with generous negative "
            "space. Editorial and restrained, not busy."
        ),
        "minimal": (
            "MINIMAL. Near-empty near-white field, the title set modestly in "
            "ink, one small accent detail. Maximum restraint."
        ),
    }

    def _cover_system(self, style: str) -> str:
        direction = self._STYLE_DIRECTIONS.get(style, self._STYLE_DIRECTIONS["editorial"])
        return (
            "You are a senior art director and SVG engineer for Ashford & Briggs, "
            "maker of Paladin (real-time AI intelligence for recruiting phone "
            "calls). You hand-write clean, production SVG for blog header images.\n\n"
            "BRAND & PALETTE (light, airy, high-end — use ONLY these colors):\n"
            "- Grounds: #fcfeff (base), #f4f7fb / #f7fafe (soft panels)\n"
            "- Ink / text: #1a1c1f ; muted #5c5e61 ; dim #6b6e72\n"
            "- Accent blue: #0076d1 ; bright #0085ea ; deep #0064b3\n"
            "- Secondary (sparingly): #6044cd\n"
            "- Hairlines: #dee1e5 / #c3c6c9\n"
            "Typography: font-family=\"Geist, 'Segoe UI', -apple-system, sans-serif\" "
            "for display text; a monospace family for the eyebrow.\n\n"
            f"DIRECTION: {direction}\n\n"
            "HARD REQUIREMENTS:\n"
            "1. Output a SINGLE self-contained <svg> with viewBox=\"0 0 1200 630\" "
            "(the social/header ratio). Do NOT set width/height attributes.\n"
            "2. ALL geometry must sit inside the viewBox. Fill the whole canvas "
            "with a ground color first.\n"
            "3. Include a descriptive <title> element for accessibility.\n"
            "4. NO <script>, NO event handlers (on*), NO <foreignObject>, NO "
            "<image> or embedded raster, NO external references (no http(s) urls, "
            "no remote fonts, no url() to anything external).\n"
            "5. Keep it clean and light — few, well-placed shapes and lots of "
            "whitespace. Do NOT make a glossy, gradient-heavy 'app-icon' badge; "
            "this is refined editorial design, not a logo sticker.\n"
            "6. XML-escape text content (& becomes &amp;, < becomes &lt;).\n\n"
            "OUTPUT CONTRACT: respond with ONLY the raw SVG markup — start with "
            "<svg and end with </svg>. No prose, no explanation, no code fences."
        )

    async def cover_image(self, title: str, brief: str = "", style: str = "editorial",
                          adjustments: str = "", current_svg: str | None = None) -> str:
        """Generate → sanitize → validate → (repair once) an on-brand SVG header.

        If both `adjustments` and `current_svg` are provided (non-empty), this
        revises the given SVG instead of generating a new one from scratch.
        Otherwise this behaves exactly as a from-scratch generation.

        Returns sanitized SVG markup. Raises AIServiceError if a valid SVG could
        not be produced after one repair attempt."""
        system = self._cover_system(style)

        if adjustments.strip() and current_svg and current_svg.strip():
            user = (
                f'Post title: "{title}"\n'
                + (f"Context / subject: {brief}\n" if brief.strip() else "")
                + "\nHere is the current image:\n"
                f"{current_svg.strip()}\n\n"
                "Here are the requested changes:\n"
                f"{adjustments.strip()}\n\n"
                "Revise the current image to apply ONLY the requested changes "
                "above. Preserve the existing design intent, composition, and "
                "any elements not covered by the requested changes — this is a "
                "targeted revision, not a new, unrelated image. Return a "
                "complete, valid, revised SVG. Return ONLY the SVG."
            )
        else:
            user = (
                f'Post title: "{title}"\n'
                + (f"Context / subject: {brief}\n" if brief.strip() else "")
                + "\nDesign the header now. Return ONLY the SVG."
            )

        return await self._generate_svg(system, user)

    async def _generate_svg(self, system: str, user: str) -> str:
        """Shared generate → sanitize → validate → (repair once) pipeline used
        by both from-scratch and revision cover-image prompts."""
        raw = await self._call(system, user, max_tokens=3000)
        svg = sanitize_svg(extract_svg(raw) or "")
        ok, reason = validate_svg(svg)
        if ok:
            return svg

        # Targeted repair: hand the model back its own attempt + the specific
        # failure and ask for a corrected SVG (single retry, then give up).
        repair_user = (
            f"{user}\n\nYour previous attempt was rejected: {reason}\n"
            "Here is that attempt:\n"
            f"{(extract_svg(raw) or raw)[:6000]}\n\n"
            "Return a corrected SVG that satisfies every hard requirement. "
            "ONLY the SVG."
        )
        raw2 = await self._call(system, repair_user, max_tokens=3000)
        svg2 = sanitize_svg(extract_svg(raw2) or "")
        ok2, reason2 = validate_svg(svg2)
        if ok2:
            return svg2
        raise AIServiceError(
            "The header generator could not produce a valid image. Please try "
            "again or adjust the brief."
        )


anthropic_service = AnthropicService()
