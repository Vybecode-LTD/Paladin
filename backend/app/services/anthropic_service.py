"""Server-side Anthropic proxy. The API key NEVER reaches the browser —
the admin frontend calls our /api/admin/ai/* routes, which call this."""
import httpx
from app.core.config import settings

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


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
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(ANTHROPIC_URL, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
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


anthropic_service = AnthropicService()
